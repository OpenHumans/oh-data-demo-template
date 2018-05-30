# Template and working demo for adding data to an Open Humans project. Python 3; Django 2.

[![Build Status](https://travis-ci.org/OpenHumans/oh-data-demo-template.svg?branch=master)](https://travis-ci.org/OpenHumans/oh-data-demo-template)

> Work through this guide to add a data source to Open Humans

## Table of Contents

- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [About this repo](#about-this-repo)
- [Introduction](#introduction)
    + [Workflow overview](#workflow-overview)
    + [How does an Open Humans data source work?](#how-does-an-open-humans-data-source-work)
- [Cloning this template](#cloning-this-template)
- [Setting up local environment](#setting-up-local-environment)
    + [Installing Heroku CLI](#installing-heroku-cli)
    + [Installing Redis](#installing-redis)
    + [Python](#python)
    + [pip](#pip)
    + [Virtual environments](#virtual-environments)
    + [Installing dependencies](#installing-dependencies)
- [Creating an Open Humans project](#creating-an-open-humans-project)
- [Final steps of app setup](#final-steps-of-app-setup)
- [Heroku deployment](#heroku-deployment)
    + [Heroku setup](#heroku-setup)
    + [Creating a Heroku application](#creating-a-heroku-application)
    + [App configuration](#app-configuration)
- [Adding dummy data](#adding-dummy-data)
- [Next steps](#next-steps)
    + [Under the hood](#under-the-hood)
    + [Editing the template](#editing-the-template)
- [Getting help](#getting-help)


### Requirements

- Python 3 & pip
- Redis
- heroku cli
- pipenv

### Quickstart

This is a very high level overview of the commands needed to set this project up from scratch, if you already have the dependencies already installed. Read below instructions for the local setup explained in more detail.

```sh
git clone git@github.com:OpenHumans/oh-data-demo-template.git
cd oh-data-demo-template
cp env.example .env
# now, edit your .env file and update it with your client id/secret, etc
pipenv install
pipenv run python manage.py migrate
pipenv run heroku local
# go to http://localhost:5000/ and the template should be running
```

## About this repo

### Introduction

This repository is a template for, and working example of an Open Humans data source. If you want to add a data source to Open Humans, we strongly recommend following the steps in this document to work from this template repo.

### Workflow overview

- First get this demo project working. Detailed instructions can be found in the [SETUP.md file](SETUP.md), but this involves the following steps:
  - clone this template repo to your own machine
  - set up your local development environment
  - create an OAuth2 project on Open Humans website
  - finalise local app setup and remote Heroku deployment
  - try out adding dummy data as a user
- When you have successfully created an Open Humans project and added dummy data using this template, you can start to customise the code to to add your desired data source. This will vary depending on your project needs, but the following hints may help you to get started:
  - the template text in `index.html` can be edited for your specific project, but mostly this file can remain as it is, to enable user authentication
  - data should be added after the user is directed back from Open Humans to `complete.html`
  - we recommend starting by looking at the function `add_data_to_open_humans` in the `tasks.py` file


### How does an Open Humans data source work?

This template is a [Django](https://www.djangoproject.com/)/[Celery](http://www.celeryproject.org/) app that enables the end user - an Open Humans member - to add dummy data to an Open Humans project. The user arrives on the app's landing page (`index.html`), and clicks a button which takes them to Open Humans where they can log in (and create an account if necessary). Once logged in to the Open Humans site, the user clicks another button to authorize this app to add data to their Open Humans account, they are then returned to this app (to `complete.html`) which notifies them that their data has been added and provides a link to the project summary page in Open Humans.

So let's get that demo working on your machine, and you should be able to complete those steps as a user by running the app, before moving on to edit the code so it adds your custom data source instead of a dummy file.

#### This gif shows the completed app being used to add dummy data to an Open Humans project:

![](https://cl.ly/0s2i2J3i191d/demo-gif.gif)

## Setup

Please see [SETUP.md](SETUP.md) for detailed repo setup instructions. Quick setup is above if you have the requirements already installed on your system.

## tasks.py functions explained

## `process_datasource()`
This task solves both the problem of hitting API limits as well as the import of existing data.
The rough workflow is

```
get_existing_datasource(…)
get_start_date(…)
remove_partial_data(…)
try:
  while *no_error* and still_new_data:
    get more data
except:
  process_datasource.async_apply(…,countdown=wait_period)
finally:
  replace_datasource(…)
```

### `get_existing_datasource`
This step just checks whether there is already older `datasource` data on Open Humans. If there is data
it will download the old data and import it into our current workflow. This way we already know which dates we don't have to re-download from `datasource` again.

### `get_start_date`
This function checks what the last dates are for which we have downloaded data before. This tells us from which date in the past we have to start downloading more data.

### `remove_partial_data`
The datasource download works on a ISO-week basis. E.g. we request data for `Calendar Week 18`. But if we request week 18 on a Tuesday we will miss out on all of the data from Wednesday to Sunday. For that reason we make sure to drop the last week during which we already downloaded data and re-download that completely.

### getting more data.
Here we just run a while loop over our date range beginning from our `start_date` until we hit `today`.

### `except`
When we hit the datasource API rate limit we can't make any more requests and the exception will be raised. When this happens we put a new `process_datasource` for this user into our `Celery` queue. With the `countdown` parameter we can specify for how long the job should at least be idle before starting again. Ultimately this serves as a cooldown period so that we are allowed new API calls to the `datasource API`.

### `finally: replace_datasource`
No matter whether we hit the API limit or not: We always want to upload the new data we got from the datasource API back to Open Humans. This way we can incrementally update the data on Open Humans, even if we regularly hit the API limits.

### Example flow for `process_datasource`
1. We want to download new data for user A and `get_existing_datasource` etc. tells us we need data for the weeks 01-10.
2. We start our API calls and in Week 6 we hit the API limit. We now enqueue a new `process_datasource()` task with `Celery`.
3. We then upload our existing data from week 1-5 to Open Humans. This way a user has at least some data already available
4. After the countdown has passed our in `2` enqueued `process_datasource` task starts.
5. This new task downloads the data from Open Humans and finds it already has data for weeks 1-5. So our new task only needs to download the data for week 5-10. It can now start right in week 5 and either finish without hitting a limit again, or it will at least make it through some more weeks before crashing again, which in turn will trigger yet another new `process_datasource` task for later.

## Getting help

If you have any questions or suggestions, or run into any issues with this demo/template, please let us know, either over in [Github issues](http://github.com/OpenHumans/oh-data-source-template/issues), or at our [Slack channel](http://slackin.openhumans.org) where our growing community hangs out.