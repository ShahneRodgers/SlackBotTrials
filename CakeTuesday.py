#!/usr/bin/env python3.6
import json, os, slack, re

CHANNEL_NAME = "random"
NUM_MEMBERS_PER_WEEK = 1

class CakeTuesdayBot(slack.WebClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'TestBot'
        self.channel_name = "random"

    def start(self):
        channel = self._get_channel_by_name(self.channel_name)
        suspects = self._get_cake_tuesday_players(channel)
        accused = self._determine_least_recently_sacrificed(channel, set(suspects))
        self._convict_freeloaders(accused)

    def _get_cake_tuesday_players(self, channel):
        return self.conversations_members(channel=channel['id']).data['members']

    def _determine_least_recently_sacrificed(self, channel, suspects):
        my_messages = self._get_my_previous_messages(channel)
        for message in my_messages:
            if len(suspects) <= NUM_MEMBERS_PER_WEEK:
                return suspects
            previous = self._get_tagged_in_message(message)
            suspects -= set(previous)
            import pdb; pdb.set_trace()
            while len(suspects) < NUM_MEMBERS_PER_WEEK:
                # FIXME: should be based on what was removed from suspects earlier only
                # and probably randomised
                suspects.add(previous.pop())

        if len(suspects) > NUM_MEMBERS_PER_WEEK:
            return list(suspects)[:NUM_MEMBERS_PER_WEEK]

    def _get_my_previous_messages(self, channel):
        history = self.conversations_history(channel=channel['id'], limit=1000).data
        return [m for m in history['messages'] if m.get('username', None) == self.name]

    def _get_tagged_in_message(self, message):
        try:
            return re.findall('<@([^>]+)>', message['text'])
        except:
            import pdb; pdb.set_trace()

    def _convict_freeloaders(self, sacrifices):
        user_mentions = " & ".join([f"<@{u}>" for u in sacrifices])
        message = f"{user_mentions} are responsible for Cake Tuesday this week. Don't mess it up!"
        self.chat_postMessage(channel=f"#{self.channel_name}", text=message)
        
    def _get_channel_by_name(self, name):
        channels = self.conversations_list().data["channels"]
        channel = [c for c in channels if c["name"] == name]
        if channel:
            return channel[0]
        return None

    

def post_message(client):
    response = client.chat_postMessage(
        channel=f'#random',
        text="Hello world!")
    print(str(response))

def get_members(client):
    channels = client.conversations_list().data["channels"]
    channel_id = [c for c in channels if c["name"] == CHANNEL_NAME][0]['id']
    return client.conversations_members(channel=channel_id).data['members']


# Program starts here
if __name__ == '__main__':
    slack_token = "xoxp-833682248498-833682248930-846008334148-dee328b475b9162cf74c7879b21811f3" #os.environ['SLACK_API_TOKEN']
    CakeTuesdayBot(token=slack_token).start()
    