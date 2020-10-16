# Python Code
# project/myapp/tasks.py

import datetime
import celery

# here we assume we want it to be run every 5 mins
@celery.decorators.periodic_task(run_every=datetime.timedelta(minutes=5)) 
def myTask():
    # Do something here
    # like accessing remote apis,
    # calculating resource intensive computational data
    # and store in cache
    # or anything you please
    print 'This wasn\'t so difficult'
    return None

# A periodic task that will run at 5:30am every day
@periodic_task(run_every=(crontab(hour="05", minute="30", day_of_week="*")))
def task_example():
    logger.info("Task started")
    # add code
    logger.info("Task finished")
    return None
