QUICKSILVER-6 Team Project

## Team members
The members of the team are:
- Amey Tripathi
- Hugo Khan
- Robert Smith
- Joachim Siallagan
- Dhruv Deb

## Project structure
The project is called `recipify`.  It currently consists of a single app `recipes`.

## Deployed version of the application
The deployed version of the application can be found at [*enter url here*](*jansonsport.pythonanywhere.com*).

## Paste the above link into a browser to see the deployed website.

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.  The project source code has been developed using Python 3.12, so you are recommended to use the same version.  From the root of the project:

```
$ python3.12 -m venv venv
$ source venv/bin/activate
```

If your system does not have `python3.12` installed and you are unable to install Python 3.12 as a version you can explicitly refer to from the CLI, then replace `python3.12` by `python3` or `python`, provide this employs a relatively recent version of Python.

Install all required packages:

```
$ pip3 install -r requirements.txt
```

Migrate the database (it has already been left in for you but still follow the instructions):

```
$ python3 manage.py makemigrations
$ python3 manage.py migrate
```

Seed the development database with:

```
$ python3 manage.py seed
```

Seed the images into the website for all recipes:
```
$ python3 manage.py populate_images --overwrite
```

Enable Admin via user @johndoe:
```
$ python3 make_admin.py
```

Run the website:
```
$ python3 manage.py runserver
```

Run all tests with:
```
$ python3 manage.py test
```

## Google OAuth & AI Chef set-up
All keys have been provided in the .env file, there is no need to change anything, this will work automatically


*The above instructions should work in your version of the application.  If there are deviations, declare those here in bold.  Otherwise, remove this line.*

## Sources
The packages used by this application are specified in `requirements.txt`

*Declare are other sources here, and remove this line*
