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

Concerned citizens and impacted residents don't have a straightforward way of 
knowing what or how policies and regulations impact them or what they can do 
in response.  A community leader could use this tool to help motivate their
social followers.  Our target user will be referred to as "advocate".

### Hills (who, what, and wow)

1. Advocates are aware of policy that is being considered that is 
highly impactful to them, without needing to follow every vote.

2. Advocates are able to understand the specific impact of proposed 
policy on them without being a legal expert.

3. Advocates are able to share opinions so they can influence policy 
decisions before they are finalized.

4. Advocates can easily ascertain the voting record themes or trend of their
elected officials and political candidates without prior knowledge of who
they are.

5. Policy makers have visibility into how diverse citizenry will be impacted
by multiple variations of a proposed policy.

# Our Solution - Fix Politics App

Fix Politics is a web-based application written in Python programming
language, using the Django framework and Bootstrap user interface styling. Its 
primary goal is to help advocates find and summarize legislation based on an
advocate's preferences for impact areas and geographical location. 

The application is customizable, allowing application staff to specify
the location hierarchy and impact categories.  Complex legislation is curated, 
resulting in classifying the location scope and impact area, with a brief 
laymen-readable title and summary.

By classifying legislation by impact and location, we hope to increase 
awareness of current and pending legislation and their ability to affect change 
through voting or other activism.

## Steps to deploy the Fix Politics application

### Staged Deployment

This project is designed for three deployment stages.

1. [Development](docs/STAGE1.md)

In stage 1, each developer has their own copy of application code and
data, using SQLite3 that stores the entire database in a single file.
Django provides a development webserver to allow local testing.

2. [Pre-Production](docs/STAGE2.md)

In stage 2, each developer has their own copy of application code, but
a shared database, using Postgresql running in the IBM Cloud.  The
developer can choose to use the Django development webserver, or try out
the production server called Gunicorn.  The difference is that Django
is designed for single-user, and Gunicorn for concurrent multiple users.

3. [Production](docs/STAGE3.md)

In stage 3, the application is running in the IBM Cloud in one pod, using the
Postgresql running in the IBM Cloud from pre-production.  Updates to the
code are deployed using a Tekton pipeline.


### Setting up a Mailtrap account

To test the Send Results e-mail functionality, you can set up a free Mailtrap 
account using the steps below.  This can be used in all stages of deployment.

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

3. When you click "Send Results" from the app, your results should be e-mailed
to your Mailtrap inbox.


## License

This sample application is licensed under the Apache License, Version 2. 
Separate third-party code objects invoked within this code pattern are 
licensed by their respective providers pursuant to their own separate 
licenses. Contributions are subject to the [Developer Certificate of Origin, 
Version 1.1](https://developercertificate.org/) and the [Apache License, 
Version 2](https://www.apache.org/licenses/LICENSE-2.0.txt).

[Apache License 
FAQ](https://www.apache.org/foundation/license-faq.html#WhatDoesItMEAN)
