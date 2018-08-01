## Item Catalog
Udacity FSND catalog Flask app

This exercise focuses on building an app using the Flask framework in python to build a simple web app with a sql server that allows for CRUD operations.
This app also implements 3rd party authorization via OAuth2 using Google. The app also uses the Yelp API to allow users to create/edit/modify/delete lists of Yelp businesses.

The project also makes use of the Vagrant/VirtualBox VM environment, although it can be deployed as easily in a python virtualenv (instructions only included below for Vagrant).

----
## Getting started

**I. Setting up VM**

To get everything up and running, we'll need to install VirtualBox and Vagrant. If you have already done this, skip to the next section.

1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads), install the platform package.
2. Install [Vagrant](https://www.vagrantup.com/downloads.html), then run `vagrant --version` in your terminal to confirm proper installation (it should say something like `Vagrant 2.0.0`.
3. Clone the VM config files from the Udacity [repository](https://github.com/udacity/fullstack-nanodegree-vm) to your local environment. Then from your terminal, navigate to the `vagrant` subdirectory and run `vagrant up`. This will initiate the download and setup of the vagrant linux environment.
4. Once that's completed, run `vagrant ssh` from the `vagrant` subdirectory to log into the VM to confirm proper setup.

![vagrant ssh success](https://d17h27t6h515a5.cloudfront.net/topher/2017/April/58fa90dd_screen-shot-2017-04-21-at-16.06.30/screen-shot-2017-04-21-at-16.06.30.png)(*source: Udacity tutorial*)

**II. Adding your API credentials**

This application uses 2 json files to store client secrets for accessing the Google API for logins and the Yelp API for searches.

###For Google API:
(Note: for the login to work correct, client must enable "Accept third-party cookies and site data" in their browser.)

In the top directory, you will need to create a file: "google\_client\_secrets.json":
>
    {"web":{"client_id":"(your info here)","project_id":"(your info here)","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://accounts.google.com/o/oauth2/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":”(your info here)","redirect_uris":["(your info here)"],"javascript_origins":["(your info here)"]}}

Additional instructions from Google [here](https://developers.google.com/identity/protocols/OAuth2WebServer). You will need to create a new project on the [Google Cloud Platform console](https://console.cloud.google.com), then in the "API & services" menu, go to "Credentials", then "OAuth 2.0 client IDs". There, under "Authorized JavaScript origins", add "http://localhost:5000", and under "Authorized redirect URIs", add "http://localhost:5000/oauth2callback", and save.

###For Yelp API:
In the top directory, you will need to create a file: "yelp\_client\_secrets.json":
>
    {"web":{"client_id":"(your info here)","client_secret":"(your info here)"}}

Additional instructions from Yelp [here](https://www.yelp.com/developers/documentation/v3). You will need to create an app with Yelp to receive a Client ID + Client Secret codes to plug into the "yelp\_client\_secrets.json" file.


**III. Running the code from this repo**

1. Clone this repo into the directory where your vagrant vm has set up.
2. Log in to the vagrant VM, go to the catalog directory, create your client secret json files, and run:


>
    python database_setup.py
(first time only)

>
    python catalog.py

If the program runs correctly, you should be able to view the app from your browser and going to (http://localhost:5000).
