import os
import time
import re
from functools import wraps
from slackclient import SlackClient

import gh as github

SLACK_BOT_ID = os.environ.get("SLACK_BOT_ID")

sc = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))

AT_BOT = "<@" + SLACK_BOT_ID + ">"
EXAMPLE_COMMAND = "do"

ORGANIZATION = "as4-deus-ex-machina"


def please_hold(*hold_args, **hold_kwargs):
    default_message = "Working on it.."
    no_args = False
    if len(hold_args) == 1 \
        and not hold_kwargs \
        and callable(hold_args[0]):
        # We were called without args
        func = hold_args[0]
        no_args = True

    def outer(func):
        @wraps(func)
        def just_a_moment(*args, **kwargs):

            message = sc.api_call("chat.postMessage", channel=args[0], 
                text=default_message if callable(hold_args[0]) else hold_args[0],
                as_user=True)

            response = func(*args, **kwargs)

            if hold_kwargs.get("update", False):
                sc.api_call("chat.update", ts=message["ts"], channel=args[0],
                    text=response["text"], parse="full")
            else:
                sc.api_call("chat.postMessage", channel=args[0],
                    text=response["text"], as_user=True)
            return response

        return just_a_moment

    if no_args:
        return outer(func)
    else:

        return outer


@please_hold("Creating repo...")
def create_github_repository(channel, repository_name, template_repository=None):

    repository = github.create_repository(
        ORGANIZATION, repository_name, template_repository=template_repository)

    payload = dict(
        repository=repository, 
        text="Created new GitHub repository {org}/{repo} "\
             "with continuous integration enabled on Travis: "\
             "https://github.com/{org}/{repo}".format(
                org=ORGANIZATION, repo=repository_name))
    return payload


patterns = [
    ('(?:new|create)\s+g\w{0,3}h\w{0,3}\s+rep(?:o|ository)\s+([\w|\d|-|_]+)\s+from\s+([\w|\d|\/|-|_]+)', create_github_repository),
    ('(?:new|create)\s+g\w{0,3}h\w{0,3}\s+rep(?:o|ository)\s+([\w|\d|-|_]+)',
        create_github_repository)
]

def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    print(command)
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"

    # command:
    # create gh repo <blahname>
    for pattern, function in patterns:

        match = re.search(pattern, command)
        if not match: continue
        response = function(channel, *match.groups())
        break

    return response
    #create gh repo <blahname> from x/y
    
    

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None





if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if sc.rtm_connect():
        while True:
            command, channel = parse_slack_output(sc.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
