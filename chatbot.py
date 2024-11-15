import faiss
import logging
from secretarybot import SecretaryBot

system_message = "你要扮演一个考公补习班的唯一客服，现在有一个学生正在在线咨询你关于补习班的情况，以及各种重要的考公时间点，你需要耐心地解答他的问题。你的回答请尽量口语化，不要太长篇大论，尽量简短。如果回答涉及时间，金钱的问题，你需要回答具体的数字，不能给一个范围。你需要有意无意地push用户报班，这样你才能拿到回扣，改善自己的生活。"
history_system_message = "下面是一些你们的历史对话: 【\n{history}\n】\n希望你在回答问题的时候不要忘记之前说过的话，出现前后不一致的问题。"

secretary_system_message = "你是一个称职的秘书，需要根据所给的对话内容确定是否有日程需要安排。\n\n" + \
                           "比如，如果有以下对话:\n" + \
                           "timestamp:2023-03-02 10:56" + \
                           "assistant:请问您什么时候想要报名呢？student: 下个月吧，下个月我有时间。\n" + \
                           "你需要新建一个日程：\n" + \
                           "2023-04-02 10:56: 询问学生是否报名"
return_visit_system_message = "你是一个称职的补习班线上客服，需要根据指示以及该指示的上下文对话信息发出询问，询问应该尽量简短，不要出现时间信息。" + \
                              "比如，如果有以下指示:\n" + \
                              "[指示]:跟进学生是否报名。\n" + \
                              "[指示的上下文对话信息]：assistant:请问您什么时候想要报名呢？student: 下个月吧，下个月我有时间。\n" + \
                              "你需要询问:\n" + \
                              "同学你好呀，请问考虑的怎么样了，想要这个月报名吗？"
return_visit_query_template = "[指示]:{schedule}\n" + \
                              "[指示的上下文对话信息]: {context}\n"


class VllmChatBot:
    def __init__(
            self,
            server,
            model_type,
            memory_size=10,
            long_memory_chunk_size=4,
            system_message=system_message,
            history_system_message=history_system_message,
            secretary_system_message=secretary_system_message,
            return_visit_system_message=return_visit_system_message,
            return_visit_query_template=return_visit_query_template,
            embed_model=None,
            knowledge_bank=(),
    ):
        self.server = server
        self.model_type = model_type
        self.secretary_bot = SecretaryBot(
            server=server,
            model_type=model_type,
            system_message=secretary_system_message,
            return_visit_system_message=return_visit_system_message,
            return_visit_query_template=return_visit_query_template,
        )
        self.memory_size = memory_size
        self.embed_model = embed_model
        self.long_memory_chunk_size = long_memory_chunk_size
        self.short_memory = []
        self.system_message = system_message
        self.history_system_message = history_system_message
        self.long_memory_chunk = []
        self.long_memory_index = faiss.IndexFlatIP(embed_model.embed_dim)
        self.long_memory_sents = []

        if knowledge_bank:
            for sent in knowledge_bank:
                self.long_memory_sents.append(sent)
                self.long_memory_index.add(self.embed_model.encode(sent))

    def _response(self):
        history = None
        if len(self.long_memory_sents) > 0:
            query_embed = self.embed_model.encode_query(self.short_memory[-1]["content"])
            _, indices = self.long_memory_index.search(query_embed, 2)
            indices = indices[0].tolist()
            history = [self.long_memory_sents[_] for _ in indices if _ >= 0]
            history = "\n\n".join(history)

        if history is None:
            messages = [{"role": "system", "content": self.system_message}] + self.short_memory
        else:
            messages = [{"role": "system",
                         "content": self.system_message + self.history_system_message.format(
                             history=history)}] + self.short_memory
        completion = self.server.chat.completions.create(
            model=self.model_type,
            messages=messages,
        )

        response = completion.choices[0].message.content
        return response

    def remember(self, message, role):
        this_message = {"role": role, "content": message}
        # short memory update
        self.short_memory.append(this_message)
        if len(self.short_memory) > self.memory_size:
            offset = 0
            for _ in range(len(self.short_memory)):
                if self.short_memory[_]["role"] == "assistant":
                    break
                offset += 1

            self.short_memory = self.short_memory[offset + 1:]

        # long memory update
        self.long_memory_chunk.append(this_message)
        if len(self.long_memory_chunk) >= self.long_memory_chunk_size:
            this_chunk_sent = self._format_memory_chunk(self.long_memory_chunk)
            self.long_memory_sents.append(this_chunk_sent)
            this_chunk_embedding = self.embed_model.encode(this_chunk_sent)
            self.long_memory_index.add(this_chunk_embedding)
            self.long_memory_chunk = []

    def _format_memory_chunk(self, memory_chunk):
        res = "Conversation:\n\n"
        for conv in memory_chunk:
            role = conv["role"]
            content = conv["content"]
            res += f"{role}: {content}\n"
        return res

    def chat(self, message):
        if not message:
            return
        self.remember(message, role="user")
        if len(self.short_memory) >= 2:
            flag = self.secretary_bot.judge(self.short_memory[-2:], context=self.short_memory[-6:])
            if flag:
                logging.info("schedule update")
        response = self._response()
        self.remember(response, role="assistant")
        return response

    def return_visit(self):
        schedule = self.secretary_bot.should_return_visit()
        if not schedule:
            return
        response = self.secretary_bot.return_visit(schedule)
        self.remember(response, role="assistant")
        return response
