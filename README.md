# Emb(race): Policy and Legislation Reform

Technology has the power to drive action. And right now, a call to action is
needed to eradicate racism. **Black lives matter.**

We recognize technology alone cannot fix hundreds of years of racial injustice
and inequality, but when we put it in the hands of the Black community and
their supporters, technology can begin to bridge a gap. To start a dialogue.
To identify areas where technology can help pave a road to progress.

This project is an effort to utilize technology to analyze, inform, and
develop policy to reform the workplace, products, public safety, and
legislation.

This is one of three open source projects underway as part of the [Call for 
Code Emb(race) Spot Challenge](https://github.com/topics/embrace-call-for-code) 
led by contributors from IBM and Red Hat.

## Problem statement

Concerned and impacted citizens don't have a straightforward way of knowing
what or how policies and regulations impact them or what they can do in
response.

### Hills (who, what, and wow)

1. Citizens are aware of policy that is being considered that is highly
impactful to them, without needing to follow every vote.

2. Citizens are able to understand the specific impact of proposed policy on
them without being a legal expert.

3. Citizens are able to share opinions so they can influence policy decisions
before they are finalized.

4. Citizens can easily ascertain the voting record themes or trend of their
elected officials and political candidates without prior knowledge of who
they are.

5. Policy makers have visibility into how diverse citizenry will be impacted
by multiple variations of a proposed policy.

# Our Solution - Fix Politics App

Fix Politics is a web-based application developed with Python and Django. Its primary goal is to find, classify, and summarize legislation based on a user's preferences for impacted subject areas and geographical location. Natural Language Processing and Machine Learning allow Fix Politics to interpret complex legislation that is often difficult for the average citizen to understand. By classifying legislation into Impact areas, we hope to increase citizen awareness of current and pending legislation and their ability to affect change through voting.

## Steps to deploy the Fix Politics application

#### Native Application Development

1. Download and install the following modules.

* [Python](https://www.python.org/downloads/)
* [Pipenv](https://pypi.org/project/pipenv/)
* [Gunicorn](https://docs.gunicorn.org/en/stable/index.html)

2. Clone this GitHub repo to your local environment.

```bash
git clone https://github.com/Call-for-Code/Embrace-Policy-Reform.git
```

3. Running Django applications has been simplified with a `manage.py` file to avoid dealing with configuring environment variables to run your app. From your project root, you can download the project dependencies with:

```bash
pipenv install
```

4. Activate your project's virtual environment with:

```bash
pipenv shell
```

5. Run the application locally in one of the following two ways:

To run as a Development server (py and HTML changes will automatically be picked up):

```bash
./run
```

To run as a Production server (shut down and restart required to pick up changes):

```bash
./app.sh
```

6. Your application will be running at `http://localhost:3000`.  You can access the `/health` endpoint at the host to verify server and app health.

##### Debugging locally
To debug a Django project run `python manage.py runserver 3000` with DEBUG set to True in `settings.py` to start a native Django development server. This comes with the Django's stack-trace debugger, which will present runtime failure stack-traces. For more information, see [Django's documentation](https://docs.djangoproject.com/en/2.0/ref/settings/).

##### Setting up a Mailtrap account
To test the Send Results e-mail functionality, you can set up a free Mailtrap account using the steps below.

1. Go to [Mailtrap](https://mailtrap.io/) and sign up for a free account.

2. Go to your Demo Inbox and copy your credentials:
```bash
user_name => 'your_username',
password => 'your_password',
address => 'smtp.mailtrap.io',
domain => 'smtp.mailtrap.io',
port => '2525',
```

3. In your virtual environment, export your credentials:
```bash
export EMAIL_HOST='smtp.mailtrap.io'
export EMAIL_HOST_USER='your_username'
export EMAIL_HOST_PASSWORD='your_password'
export EMAIL_PORT='2525'
```

4. Start the app:
```bash
./run

or

./app.sh
```

5. When you click "Send Results" from the app, your results should be e-mailed to your Mailtrap inbox.

## License

This sample application is licensed under the Apache License, Version 2. Separate third-party code objects invoked within this code pattern are licensed by their respective providers pursuant to their own separate licenses. Contributions are subject to the [Developer Certificate of Origin, Version 1.1](https://developercertificate.org/) and the [Apache License, Version 2](https://www.apache.org/licenses/LICENSE-2.0.txt).

[Apache License FAQ](https://www.apache.org/foundation/license-faq.html#WhatDoesItMEAN)
