# Legalzard Bot

This is a Python Flask Webhook that acts as a bot to check for incompatible licenses in a GitHub repository's dependencies and create an issue if any are found. The bot uses the `Github` and `requests` libraries to access the repository and its dependencies. It also uses the `doWellOpensourceLicenseCompatibility` library to check for license compatibility.

## Installation

1. Clone the repository to your local machine
2. Install the required libraries using `pip install -r requirements.txt`
3. Replace `<github-app-id>` with your GitHub App ID and `<local-githug-privatekey>` with the path to your GitHub App private key file.
4. Replace `<api-key>` with your doWell API key.
5. Deploy the Webhook to a server or cloud platform (e.g render.com).
6. Create new github app. Pass in the live address as the webhook and
7. Configure the `Meta`, `Issues` and `Content` permissions

## Creating and Configuring the Github App

1. Log in to your GitHub account.
2. Go to your account settings and click on **Developer settings**.
3. Click on **GitHub Apps** and then **New GitHub App**.
4. Fill out the required fields such as the app name, description, webhook and homepage URL.
5. Configure the app permissions, events,  and installation options.
6. Generate a private key and store it securely. The path to the private key file should be provided in place of the `<local-githug-privatekey>`
7. Install the GitHub App on the repositories you want to monitor.
8. Use the app's credentials to authenticate and access the GitHub API. It should be used in place of the `<github-app-id>`

For more detailed instructions, you can refer to the official [GitHub documentation on creating and configuring GitHub apps](https://docs.github.com/en/developers/apps/creating-a-github-app).


## Usage

1. Install the GitHub App on the repositories you want to monitor.
2. Whenever a new pull request is created, the bot checks for incompatible licenses in the repository's dependencies.
This is done with the following steps:
- Gets the licence ID from the REPO
- Gets te owner's name from the repo, and uses it to get the owner's email from the `https://api.github.com/users/{owner}` endpoint
- Runs the github authorization
- Gets the repo's dependencies
- Separates each license and adds them to a set
- Gets all the available licenses from spdx.org as a json file
- Using the `doWellOpensourceLicenseCompatibility`'s search function, gets the first icence in the list
- Runs the `doWellOpensourceLicenseCompatibility`'s `check_compatibility` function against each successive licence (if the first occurance is not compatible), but using the eventID obtained after using the licence name from the search function.
- If the user's email is not null, the webhook will send an email with the list of incompatible licences to the owner's email.

3. If any incompatible licenses are found, the bot creates an issue titled "Incompatible Licenses" and lists all incompatible licenses in the issue body.

## Limitations

This Webhook only checks for incompatible licenses in the repository's direct dependencies and does not check for transitive dependencies. It also requires a valid Dowell API key to function properly.