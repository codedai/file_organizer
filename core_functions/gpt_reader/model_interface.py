import openai


class ModelInterface(object):

    def __init__(self) -> None:
        pass

    def send_msg(self, *args):
        pass


class OpenAIModel(object):

    def __init__(self, api_key, model='gpt-3.5-turbo-0301', temperature=0.2) -> None:
        openai.api_key = api_key
        self.model = model
        self.temperature = temperature

    def send_msg(self, msg: list[dict]):

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=msg,
            temperature=self.temperature
        )

        return response
