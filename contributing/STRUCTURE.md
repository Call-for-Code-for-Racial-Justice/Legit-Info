## Understanding the Structure of this Project

### Django

![Django](basic-django.png)

Django provides a framework for Python applications.  Our application
has three main directories.  `cfc_project` for the entire project, 
`fixpol` for the main application, and `users` for user access management.
The `manage.py` is Python's administration program.  Output CSV files are
stored in `results` directory.


```bash
.
├── db.sqlite3
├── cfc_project
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── fixpol
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_impact.py
│   │   ├── 0003_location_hierarchy.py
│   │   ├── 0004_auto_20200803_0641.py
│   │   ├── 0005_location_shortname.py
│   │   ├── 0006_location_parent.py
│   │   ├── 0007_profile.py
│   │   ├── 0008_delete_profile.py
│   │   ├── 0009_auto_20200804_2241.py
│   │   ├── 0010_searchcriteria.py
│   │   ├── 0011_auto_20200805_1926.py
│   │   ├── 0012_auto_20200805_1939.py
│   │   ├── 0013_auto_20200805_1948.py
│   │   ├── 0014_auto_20200806_0238.py
│   │   ├── 0015_law.py
│   │   ├── 0016_auto_20200808_2031.py
│   │   ├── 0017_auto_20200808_2319.py
│   │   ├── 0018_law_key.py
│   │   ├── 0019_auto_20200809_1423.py
│   │   ├── 0020_auto_20200809_1452.py
│   │   ├── 0021_auto_20200809_1453.py
│   │   ├── 0022_auto_20200813_2141.py
│   │   ├── 0023_auto_20200813_2246.py
│   │   └── __init__.py
│   ├── models.py
│   ├── templates
│   │   ├── base-beth.html
│   │   ├── base.html
│   │   ├── base-tony.html
│   │   ├── criteria.html
│   │   ├── criterias.html
│   │   ├── email-full.html
│   │   ├── email.html
│   │   ├── email-inlined.html
│   │   ├── email-results.html
│   │   ├── email-results.txt
│   │   ├── email_sent.html
│   │   ├── email.txt
│   │   ├── impacts.html
│   │   ├── index.html
│   │   ├── index-tony.html
│   │   ├── locations.html
│   │   ├── results-as-csv.txt
│   │   ├── results.html
│   │   ├── results.txt
│   │   ├── save_share.html
│   │   └── search.html
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── manage.py
├── results
│   └── RESULTS.md
└── users
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── __init__.py
    ├── migrations
    │   ├── 0001_initial.py
    │   ├── 0002_auto_20200804_1738.py
    │   ├── 0003_auto_20200804_2241.py
    │   ├── 0004_auto_20200805_1851.py
    │   ├── 0005_auto_20200805_1855.py
    │   ├── 0006_profile_criteria.py
    │   └── __init__.py
    ├── models.py
    ├── templates
    │   └── registration
    │       ├── logged_out.html
    │       ├── login.html
    │       ├── profile.html
    │       ├── register.html
    │       └── update.html
    ├── tests.py
    ├── urls.py
    └── views.py
```



### Bootstrap, CSS and UI Styling

Bootstrap is used to provide a "responsive" user iterface.  The application
can adjust among five sizes (based on the width in pixels):

* Extra small (<576px)	
* Small (>=576px)	
* Medium (>=768px)	
* Large (>=992px)	
* Extra Large (>=1200px)

Note that smartphones and tablets could be considered one size in `portrait`
mode, and a different size in `landscape` mode.

Most of the base HTML is in the template files above.  Static files that
can be cached are collected under `staticfiles` directory.


```bash
.
├── staticfiles
│   ├── admin
│   │   ├── css
│   │   │   ├── autocomplete.css
│   │   │   ├── base.css
│   │   │   ├── changelists.css
│   │   │   ├── dashboard.css
│   │   │   ├── fonts.css
│   │   │   ├── forms.css
│   │   │   ├── login.css
│   │   │   ├── responsive.css
│   │   │   ├── responsive_rtl.css
│   │   │   ├── rtl.css
│   │   │   ├── vendor
│   │   │   │   └── select2
│   │   │   │       ├── LICENSE-SELECT2.md
│   │   │   │       ├── select2.css
│   │   │   │       └── select2.min.css
│   │   │   └── widgets.css
│   │   ├── fonts
│   │   │   ├── LICENSE.txt
│   │   │   ├── README.txt
│   │   │   ├── Roboto-Bold-webfont.woff
│   │   │   ├── Roboto-Light-webfont.woff
│   │   │   └── Roboto-Regular-webfont.woff
│   │   ├── img
│   │   │   ├── calendar-icons.svg
│   │   │   ├── gis
│   │   │   │   ├── move_vertex_off.svg
│   │   │   │   └── move_vertex_on.svg
│   │   │   ├── icon-addlink.svg
│   │   │   ├── icon-alert.svg
│   │   │   ├── icon-calendar.svg
│   │   │   ├── icon-changelink.svg
│   │   │   ├── icon-clock.svg
│   │   │   ├── icon-deletelink.svg
│   │   │   ├── icon-no.svg
│   │   │   ├── icon-unknown-alt.svg
│   │   │   ├── icon-unknown.svg
│   │   │   ├── icon-viewlink.svg
│   │   │   ├── icon-yes.svg
│   │   │   ├── inline-delete.svg
│   │   │   ├── LICENSE
│   │   │   ├── README.txt
│   │   │   ├── search.svg
│   │   │   ├── selector-icons.svg
│   │   │   ├── sorting-icons.svg
│   │   │   ├── tooltag-add.svg
│   │   │   └── tooltag-arrowright.svg
│   │   └── js
│   │       ├── actions.js
│   │       ├── actions.min.js
│   │       ├── admin
│   │       │   ├── DateTimeShortcuts.js
│   │       │   └── RelatedObjectLookups.js
│   │       ├── autocomplete.js
│   │       ├── calendar.js
│   │       ├── cancel.js
│   │       ├── change_form.js
│   │       ├── collapse.js
│   │       ├── collapse.min.js
│   │       ├── core.js
│   │       ├── inlines.js
│   │       ├── inlines.min.js
│   │       ├── jquery.init.js
│   │       ├── popup_response.js
│   │       ├── prepopulate_init.js
│   │       ├── prepopulate.js
│   │       ├── prepopulate.min.js
│   │       ├── SelectBox.js
│   │       ├── SelectFilter2.js
│   │       ├── urlify.js
│   │       └── vendor
│   │           ├── jquery
│   │           │   ├── jquery.js
│   │           │   ├── jquery.min.js
│   │           │   └── LICENSE.txt
│   │           ├── select2
│   │           │   ├── i18n
│   │           │   │   ├── af.js
│   │           │   │   ├── ar.js
│   │           │   │   ├── az.js
│   │           │   │   ├── bg.js
│   │           │   │   ├── bn.js
│   │           │   │   ├── bs.js
│   │           │   │   ├── ca.js
│   │           │   │   ├── cs.js
│   │           │   │   ├── da.js
│   │           │   │   ├── de.js
│   │           │   │   ├── dsb.js
│   │           │   │   ├── el.js
│   │           │   │   ├── en.js
│   │           │   │   ├── es.js
│   │           │   │   ├── et.js
│   │           │   │   ├── eu.js
│   │           │   │   ├── fa.js
│   │           │   │   ├── fi.js
│   │           │   │   ├── fr.js
│   │           │   │   ├── gl.js
│   │           │   │   ├── he.js
│   │           │   │   ├── hi.js
│   │           │   │   ├── hr.js
│   │           │   │   ├── hsb.js
│   │           │   │   ├── hu.js
│   │           │   │   ├── hy.js
│   │           │   │   ├── id.js
│   │           │   │   ├── is.js
│   │           │   │   ├── it.js
│   │           │   │   ├── ja.js
│   │           │   │   ├── ka.js
│   │           │   │   ├── km.js
│   │           │   │   ├── ko.js
│   │           │   │   ├── lt.js
│   │           │   │   ├── lv.js
│   │           │   │   ├── mk.js
│   │           │   │   ├── ms.js
│   │           │   │   ├── nb.js
│   │           │   │   ├── ne.js
│   │           │   │   ├── nl.js
│   │           │   │   ├── pl.js
│   │           │   │   ├── ps.js
│   │           │   │   ├── pt-BR.js
│   │           │   │   ├── pt.js
│   │           │   │   ├── ro.js
│   │           │   │   ├── ru.js
│   │           │   │   ├── sk.js
│   │           │   │   ├── sl.js
│   │           │   │   ├── sq.js
│   │           │   │   ├── sr-Cyrl.js
│   │           │   │   ├── sr.js
│   │           │   │   ├── sv.js
│   │           │   │   ├── th.js
│   │           │   │   ├── tk.js
│   │           │   │   ├── tr.js
│   │           │   │   ├── uk.js
│   │           │   │   ├── vi.js
│   │           │   │   ├── zh-CN.js
│   │           │   │   └── zh-TW.js
│   │           │   ├── LICENSE.md
│   │           │   ├── select2.full.js
│   │           │   └── select2.full.min.js
│   │           └── xregexp
│   │               ├── LICENSE.txt
│   │               ├── xregexp.js
│   │               └── xregexp.min.js
│   ├── css
│   │   └── default.css
│   ├── django_extensions
│   │   ├── css
│   │   │   └── jquery.autocomplete.css
│   │   ├── img
│   │   │   └── indicator.gif
│   │   └── js
│   │       ├── jquery.ajaxQueue.js
│   │       ├── jquery.autocomplete.js
│   │       └── jquery.bgiframe.js
│   ├── images
│   │   ├── 404.svg
│   │   ├── arrow-right-transparent-smaller.png
│   │   └── cloud-header.png
│   └── js
│       └── bundle.js
```

### Python, Pip and Pipenv

The pipenv tool provides a virtual Python environment, so that all 
dependencies that are installed can be tracked.  The complete list
of dependencies are in `Pipfile.lock` and `requirements.txt` files.

```bash
.
├── Pipfile
├── Pipfile.lock
├── requirements.txt
├── runtime.txt
```

### Scripts

As needed, we have created a few scripts to help with common tasks.

```bash
.
├── app.sh
├── icc
├── port-forward.sh
├── run

├── run-pg
```

### Docker, Kubernetes, OpenShift, and Tekton

The application can run on any standard LAMP stack.  Instead, we used
Red Hat OpenShift to run the demo.


```bash
.
├── build-docker
├── Dockerfile
├── k8s
│   ├── deployment.yaml
│   ├── route.yaml
│   └── service.yaml
├── run-docker
├── tekton
│   ├── pipeline-resource.yaml
│   ├── pipeline.yaml
│   ├── python-pipeline.yaml
│   └── tasks.yaml
├── template_secret-db-fix-politics.env
├── template_secret-smtp-mailtrap.env
```


### Backups and Support files

Sample data files, backups of the databases and related files are
stored here.

```bash
.
│   ├── fixpol_law.sql
│   ├── fixpol_location.sql
│   ├── impact.sql
│   ├── lawdump.csv
│   ├── law.sql
│   ├── loc.sql
│   ├── london.csv
```

### Documentation

Documentation is stored in these directories.  This includes the main
README.md which then points to the rest of the files listed.  We have
attempted to make all Markdown files fit the 80-character standard, although
some URLs extend beyond that.


```bash
.
├── contributing
│   ├── basic-django.png
│   ├── CODE_OF_CONDUCT.md
│   ├── ISSUES.md
│   ├── PULL-REQUESTS.md
│   └── STRUCTURE.md
├── CONTRIBUTING.md
├── DESCRIPTION.md
├── docs
│   ├── Architecture-Fix-Politics-2020-08-26.png
│   ├── Final_presentation_-_fix_politics2.pptx
│   ├── fixpol_impact.sql
│   ├── Fix-Politics-Architecture-Aug11.pptx
│   ├── Fix-Politics-Architecture-Aug12.pptx
│   ├── Fix-Politics-Architecture-Aug16.pptx
│   ├── Fix-Politics-Aug03.pptx
│   ├── Fix-Politics-Aug04.pptx
│   ├── Fix-Politics-Aug06a.pptx
│   ├── Fix-Politics-Aug06.pptx
│   ├── Fix-Politics-Aug10-a.png
│   ├── Fix-Politics-Aug10.pptx
│   ├── Screenshot\ from\ 2020-08-10\ 18-12-39.png
│   ├── Screenshot\ from\ 2020-08-10\ 18-13-08.png
│   ├── Screenshot\ from\ 2020-08-10\ 18-13-26.png
│   ├── Screenshot\ from\ 2020-08-10\ 18-14-39.png
│   ├── Screenshots-Aug04
│   │   ├── page0002-Aug04.png
│   │   ├── page0003-Aug04.png
│   │   ├── page0004-Aug04.png
│   │   ├── page0005-Aug04.png
│   │   ├── page0006-Aug04.png
│   │   ├── page0011-Aug04.png
│   │   ├── page0012-Aug04.png
│   │   ├── page0013-Aug04.png
│   │   ├── page0014-Aug04.png
│   │   ├── page0015-Aug04.png
│   │   ├── page0021-Aug04.png
│   │   └── page0030-Aug04.png
│   ├── STAGE1.md
│   ├── STAGE2.md
│   ├── STAGE3.md
│   ├── testcases.txt
│   └── UI_designs.pptx
├── LICENSE
├── README.md
```



