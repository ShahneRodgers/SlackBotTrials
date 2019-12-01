#!/usr/bin/env python3.6
import json, os, re, time
from datetime import date
from functools import lru_cache
import slack

NUM_MEMBERS_PER_WEEK = 1

class CakeTuesdayBot(slack.WebClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'TestBot'
        self.channel_name = "test"

    def start(self):
        channel_id = self._get_channel_by_name(self.channel_name)['id']
        while self._has_sent_weeks_message(channel_id):
            time.sleep(60*60*24)
        suspects = self._get_cake_tuesday_players(channel_id)
        accused = self._determine_least_recently_sacrificed(channel_id, set(suspects))
        self._convict_freeloaders(accused)
        self.start()

    def _has_sent_weeks_message(self, channel_id):
        messages = self._get_my_previous_messages(channel_id)
        if not messages:
            return False
        last_message_date = date.fromtimestamp(float(messages[0]['ts']))
        # If it's been more than a week, we must be due for another CT.
        if (date.today() - last_message_date).days >= 7:
            return True
        # Otherwise we're only due if the last message was before Wednesday and
        # it's now Wednesday or later.
        return last_message_date.weekday() >= 3 or date.today().weekday() < 3

    def _get_cake_tuesday_players(self, channel_id):
        return self.conversations_members(channel=channel_id).data['members']

    def _determine_least_recently_sacrificed(self, channel_id, suspects):
        my_messages = self._get_my_previous_messages(channel_id)
        for message in my_messages:
            if len(suspects) <= NUM_MEMBERS_PER_WEEK:
                return suspects
            previous = set(self._get_tagged_in_message(message))
            last_removed = previous & suspects
            suspects -= previous
            while len(suspects) < NUM_MEMBERS_PER_WEEK:
                # If we don't have enough suspects left, just choose one of the
                # people who was last removed.
                suspects.add(last_removed.pop())

        if len(suspects) > NUM_MEMBERS_PER_WEEK:
            return list(suspects)[:NUM_MEMBERS_PER_WEEK]

    def _get_my_previous_messages(self, channel_id):
        history = self.conversations_history(channel=channel_id, limit=1000).data
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

    @lru_cache(maxsize=32)  
    def _get_channel_by_name(self, name):
        channels = self.conversations_list().data["channels"]
        channel = [c for c in channels if c["name"] == name]
        if channel:
            return channel[0]
        return None


# Program starts here
if __name__ == '__main__':
    slack_token = "xoxp-833682248498-833682248930-846008334148-dee328b475b9162cf74c7879b21811f3" #os.environ['SLACK_API_TOKEN']
    CakeTuesdayBot(token=slack_token).start()
    