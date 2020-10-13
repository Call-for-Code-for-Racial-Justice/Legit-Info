# Fix Politics

Fix Politics is a simple `Content Management System`, or CMS for short, that
delivers curated content to users.


## Section 1 Administration

Administration allows authorized staff to create and maintain the list of
locations, impact areas, and curated policy legislation.

### Subsection 1.1 Superuser: cfcadmin

Use the Django `createsuperuser` to create the first user.

```bash
$ cd fix-politics
$ pipenv shell
(fix) $ python manage.py createsuperuser
```

For example, create username "cfcadmin".

To access admin panels, add "/admin" to the main website.  For local
testing, use:  `http://localhost:3000/admin`

Alternatively, launch `http://localhost:3000` and sign in as "cfcadmin",
you will find an "Admin" tab on the upper right of the navigation bar.

### Subsection 1.2 Impact Areas

To access admin panels, add "/admin" to the main website.  For local
testing, use:  `http://localhost:3000/admin`  From here, you can add
or remove impact areas.  Here is an example:

* Healthcare
* Safety
* Environment
* Transportation
* Jobs

### Subsection 1.3 Locations

To access admin panels, add "/admin" to the main website.  For local
testing, use:  `http://localhost:3000/admin`  From here, you can add
or remove locations.  Here is an example:

```
United Kingdom
└─ England, UK
    └─ London County
        └─ London, England
United States
└─ Arizona, USA
    └─ Pima County, AZ
        └─ Tucson, Arizona
└─ Ohio, USA
    └─ Franklin County
        └─ Columbus, OH
```

The first entry must be `world`, with a parent of `world`, in effect pointing
to itself.  This is required for the "ancestor-search" algorithm.  For 
location hierarchies, you must enter the parent before the child.

In the above example, you must create
`United States` before you can enter `Arizona` or `Ohio`.

For `United States`, the parent is `world`
For `Ohio, USA`, the parent is `United States`
For `Franklin County`, the parent is `Ohio, USA`
For `Columbus, OH`, the parent is `Franklin County`

You may designate any location by its government level, such as `country`,
`state`, `county`, `city`, `province`, `district`, etc.


### Subsection 1.4 Laws

To access admin panels, add "/admin" to the main website.  For local
testing, use:  `http://localhost:3000/admin`  From here, you can add
or remove laws, policies, regulations and other proposed legislation.

For each piece of legislation, the curator must identify the following:

* key -- a unique value that refers to the specific legislation
* location -- the scope of location, specify the most narrow location,
for example, if legislation only applies to a city, do not specify the
county or state.  If the the legislation applies to multiple cities in 
a particular county, specify the county.
* impact -- select the impact area that is most represented by this law
* title -- phrase a laymen-readable version of the title.
* summary -- write two to four sentences that summarize the impact of this
law for this location.  This can include statistics that support this 
assessment.

Here is an example:

```
Key: AZ-SB-1682 (2020)
Location: Arizona, USA
Impact: Safety
Title: Protection requirements for foster children
Summary:  The results of background checks for each adult member of the 
foster care placement household will be used to determine danger level. 
oster children shall be kept safe from placements that constitute a Tier 5 
danger. If the department determines that a placement constitutes a tier 5 
danger, the department shall remove all foster children from this placement 
within four(24) hours after making the determination.
```

### Subsection 1.5 Staff

The cfcadmin can create additional users, referred to as `staff` that have 
selected permissions to add, modify or delete locations, impact areas, or 
curated legislation content.



## Section 2 Anonymous Search

Advocates do not need to pre-register to search for legislation.  This
is referred to as "anonymous search".

### Subsection 2.1 Initiate Search

From the home page, `http://localhost:3000` select "Search" either from
the upper right navigation bar, or the button at the bottom of screen.

Select the location, and one or more impact areas you are concerned about.

Press the "Search Legislation" button.  The process is called an 
"ancestor search" in that not only will it find legislation related to the
location specified, but also all legislation in parent governments.  For
example, if you specify "Frankin County", you would get laws from Franklin,
as well as laws that relate to Ohio overall, and USA as well, but not any
from Columbus OH as that is more specific.

### Subsection 2.2 Results Page

A list of legislation that matches the search criteria is found.  The 
anonymous advocate may choose to "Print Results", "Save CSV File", or
"Search Again".

### Subsection 2.3 Print Results

The results can be printed to PDF file or local/network printer.  The
code has added a title and removed the buttons that would normally appear
in a "browser print" function.

### Subsection 2.4 Save CSV File

The results can be downloaded as a comma-separated-variable (CSV) file.
Selecting "Download" will initiate this download.



## Section 3 Registration and Profile

To simplify repeat usage, an advocate may register their profile.  From
the home page, `http://localhost:3000` select "Register".

* First screen: enter username and password, re-enter same password.
* Second screen: enter first and last name, location and impact areas.


## Section 4 Profile Search

Registered advocates can perform search using their profile to set the
defaults.  From home page, `http://localhost:3000` select "Sign in".

Once signed in, select "Search" to initiate search screen.  The advocate
can leave the defaults as is, or modify the location and/or impact areas.

### Subsection 4.1 Results Page

The results page is similar to section 2.2, but with an additional feature:
"Send Results"

### Subsection 4.2 Send Results

When "Send Results" is selected, a confirmation screen will indicate that
the email was sent, or indicate there was a failure in the transmission.

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



## Conclusion

The project allowed contributors to learn about Python, Django and Bootstrap.

## Results

This project has completed the first three hills. 

1. Advocates are aware of policy that is being considered that is 
highly impactful to them, without needing to follow every vote.

The search can be done for a specific location, and one or more impact
areas.  This search can be done anonymously, or with a registered profile.

2. Advocates are able to understand the specific impact of proposed 
policy on them without being a legal expert.

Curated content by legal or subject matter experts can be entered by staff
to have laymen-readable title and summary for each policy.

3. Advocates are able to share opinions so they can influence policy 
decisions before they are finalized.

The search results can be printed, downloaded as CSV file, or sent to 
yourself so that it can then be forwarded onto the rest of the social 
followers.



## Acknowledgments

Team Fix Politics would like to acknowledge the assistance of Matt Perrins,
Jermaine Edwards, Victor Brown and Tedd Ginsley.
