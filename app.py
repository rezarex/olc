
import os
import re

import requests

from flask import Flask, request
from github import Github, GithubIntegration
from doWellOpensourceLicenseCompatibility import doWellOpensourceLicenseCompatibility
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
# MAKE SURE TO CHANGE TO YOUR APP NUMBER!!!!!
app_id = '407051'#'<github-app-id>'
# Read the bot certificate
path = 'C:/xampp/htdocs/vado/dowell/dennis/compatibility-bot/Opensource-License-Compatibility/keys/legaltester.pem'    #"<local-githug-privatekey>"
with open(
        os.path.normpath(os.path.expanduser(path)),
        'r'
) as cert_file:
    app_key = cert_file.read()
# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)


@app.route("/", methods=['POST'])
def legalzard_bot():
    # Get the event payload
    payload = request.json
    # get license information
    repo_license_id = payload.get('repository').get('license')
    if not repo_license_id:
        return "ok"
    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']


    #get the email from the github users endpoint, using the repo owner's name
    user_info = requests.get(f'https://api.github.com/users/{owner}')

    # email_string = user_info.json()['email']

    owner_email = 'marvin.wekesa@gmail@gmail.com'#"georgekibew@gmail.com" #sanitizeEmail(email_string)
    # owner_email = user_info.json()['email']
    print(user_info)


   # Get a git connection as our bot
    # Here is where we are getting the permission to talk as our bot and not
    # as a Python webservice
    github_auth = git_integration.get_access_token(git_integration.get_installation(owner, repo_name).id).token
    git_connection = Github(login_or_token=github_auth)
    repo = git_connection.get_repo(f"{owner}/{repo_name}")
    # get repo dependencies
    sbom_request = requests.get(f'https://api.github.com/repos/{owner}/{repo_name}/dependency-graph/sbom',
                                headers={'Authorization':f'Bearer {github_auth}','X-GitHub-Api-Version': '2022-11-28'})
    if sbom_request.status_code != 200:
        return "ok"

    sbom = sbom_request.json()
    packages = sbom.get('sbom').get('packages', [])
    package_license_ids = set()

    for p in packages:
        p_license = p.get('licenseConcluded', None)
        if p_license is None:
            continue
        # separate combined licenses
        for l in re.sub(r'\([^()]*\)', '', p_license).split(" "):
            if l not in ["AND", "OR"]:
                package_license_ids.add(l)

    # Empty set guard clause
    if len(package_license_ids) == 0:
        return "ok"
    # Get spdx license data
    spdx_request = requests.get("https://spdx.org/licenses/licenses.json")
    if spdx_request.status_code != 200:
        return "ok"

    licenses = spdx_request.json().get('licenses')
    # use the compatibility library
    # legalzard_api = doWellOpensourceLicenseCompatibility(api_key= 'bd4d19c4-1ee0-4746-9ec9-4824eb3662a3')#'<api-key>')
    # repo_license = legalzard_api.search(repo_license_id).get("data")[0]
    #print(repo_license)
    legalzard_api = doWellOpensourceLicenseCompatibility(api_key= 'bd4d19c4-1ee0-4746-9ec9-4824eb3662a3')
    repo_license = legalzard_api.search(repo_license_id).get("data")[0]
    repo_license_event_id = repo_license.get("eventId")

    #  initialize issues
    incompatible_licenses = ""
    # run comparison with package licenses
    for l_id in package_license_ids:
        try:
            # get license
            l_name = next(lnc for lnc in licenses if lnc["licenseId"] == l_id)["name"]
            # prpepare comparison data
            _pkg_license = legalzard_api.search(l_name).get("data")[0]
            _pkg_license_event_id = _pkg_license.get("eventId")
            compatibility = legalzard_api.check_compatibility({
                "license_event_id_one": repo_license_event_id,
                "license_event_id_two": _pkg_license_event_id,
            })["is_compatible"]
            # skip compatible licenses
            if compatibility:
                #incompatible_licenses += f"No issues found"
                continue
            # log incompatible licenses
            incompatible_licenses += f"{l_name}\n"
        except Exception as e:
            pass
    if incompatible_licenses == "":
        table_html = f"<h1>No compatibility issues found</h1>"
        #set email payload
        subject = "Incompatible Licenses - Legalzard Bot"
        body = table_html
        sender = "marvin.wekesa@gmail.com"
        password = "tntccgeyrevydnve"
        send_email(subject, body, sender, owner_email, password)
        return "ok"
     # prepare and write issue
    issue= f"Legalzard found licenses in your dependencies that are incompatible with your repository license\n\n {incompatible_licenses}"
    repo.create_issue(title="Incompatible Licenses", body=issue)
    print(incompatible_licenses)
    print('here')
    print(issue)
    #format the table
    table_rows = [f"<tr><td>Licence Detail</td><td>{i}</td></tr>" for i in incompatible_licenses]
    table_html = "<table>" + "".join(table_rows) + "</table>"

    #set email payload
    subject = "Incompatible Licenses - Legalzard Bot"
    body = table_html
    sender = "marvin.wekesa@gmail.com"
    password = "tntccgeyrevydnve"

    #some of the emails are not shared, in this case the repo owner will 
    # have to explicitly enable email notifications on all their repos
    # if owner_email == None:
    #     pass
    send_email(subject, body, sender, owner_email, password)
    return "ok"

def send_email(subject, body, sender, owner_email, password):
    msg = MIMEText(body, "html")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = owner_email

    # if compatibility:
    #     msg['Body'] = "No Incompatible Licences found"
    # else:
    #     msg['Body'] = body

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, owner_email, msg.as_string())
    print("Message sent!")

def sanitizeEmail(string):
        return string.replace(',','').replace('"','')

if __name__ == '__main__':
    # run server
    app.run(debug=True, port=5000)