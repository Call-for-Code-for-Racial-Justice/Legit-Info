#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
users/views.py -- Register and Display user profile information

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import logging

# Django and other third-party imports
from django.shortcuts import render, redirect
from django import forms  
from django.contrib.auth.models import User  
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.auth.forms import UserCreationForm

# Application imports
from .forms import UserForm, ProfileForm

# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

class RegisterUserForm(UserCreationForm):
  username = forms.CharField(required=True, max_length=30) 
  
  class Meta:
    model = User
    fields = ['username', 'password1', 'password2']

  def __init__(self, *args, **kwargs):
        super(RegisterUserForm, self).__init__(*args, **kwargs)
        self.fields['username'].error_messages = {'required': 'Username field is required'}
        self.fields['password1'].error_messages = {'required': 'Password field is required'}
        self.fields['password2'].error_messages = {'required': 'Password confirmation field is required.'}


def register(request):
    """Register a new user."""

    logger.info(f"Line31: {request.method}, {request.user.username}")
    if request.method != 'POST':
        # Display blank registration form.
        form = RegisterUserForm()
    else:
        # Process completed form.
        form = RegisterUserForm(data=request.POST)

        if form.is_valid():
            new_user = form.save()
            # Log the user in and then redirect to home page.
            login(request, new_user)
            return redirect('users:update')

    # Display a blank or invalid form.
    context = {'form': form}
    return render(request, 'registration/register.html', context)


@login_required
def show_profile(request):
    """Display user profile information."""

    logger.info("Line51: {request.user.username}")
    user = request.user
    # Display the location and impact preferences
    location = user.profile.location
    impacts = user.profile.impacts.all()

    context = {'user': user,
               'location': location,
               'impacts': impacts}
    return render(request, 'registration/profile.html', context)


@login_required
@transaction.atomic
def update_profile(request):
    """Update user profile information."""

    logger.info("Line68: {request.method}, {request.user.username}")
    if request.method != 'POST':
        # Pre-populate forms with previous information
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    else:
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)

        # Check updates to profile for validity
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            # import pdb; pdb.set_trace() # DEBUG
            user = request.user
            user.profile.set_criteria()
            return redirect('cfc_app:index')

    context = {'user_form': user_form,
               'profile_form': profile_form}

    return render(request, 'registration/update.html', context)
