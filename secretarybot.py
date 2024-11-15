import re
from datetime import datetime


class SecretaryBot:
    def __init__(
            self,
            server,
            model_type,
            system_message,
            return_visit_system_message,
            return_visit_query_template
    ):
        self.server = server
        self.model_type = model_type
        self.system_message = system_message
        self.return_visit_system_message = return_visit_system_message
        self.return_visit_query_template = return_visit_query_template
        self.schedules = []

    def _response(self, messages):

        completion = self.server.chat.completions.create(
            model=self.model_type,
            messages=messages,
        )

        response = completion.choices[0].message.content
        return response

    def _format_messages(self, messages):
        now = datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M")
        res = "对话:\n" + f"timestamp:{now}"
        for message in messages:
            role, content = message["role"], message["content"]
            if role == "user":
                role = "student"
            res += f"{role}:{content}"
        return res

    def judge(self, message, context):
        message = self._format_messages(message)
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": message},
        ]
        response = self._response(messages)
        match = re.search(r"(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})", response)
        if not match:
            return False
        timestamp = match.group(0)
        content = response.split(timestamp)[-1].strip(" :")
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        self.schedules.append({"timestamp": timestamp, "content": content, "context": context})
        print("update schedule: ", f"[timestamp]: {timestamp}", f"[content]: {content}")
        return True

    def should_return_visit(self):
        now = datetime.now()
        for i, schedule in enumerate(self.schedules):
            if now > schedule["timestamp"]:
                self.schedules = self.schedules[:i] + self.schedules[i + 1:]
                return schedule
        return None

    def return_visit(self, schedule):
        timestamp, content, context = schedule["timestamp"], schedule["content"], schedule["context"]
        context = self._format_messages(context)
        message = [
            {"role": "system", "content": self.return_visit_system_message},
            {"role": "user", "content": self.return_visit_query_template.format(schedule=content, context=context)},
        ]
        response = self._response(message)
        return response
