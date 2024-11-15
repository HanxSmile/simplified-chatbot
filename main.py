import threading
import time
from chatbot import VllmChatBot
from server_utils import get_vllm_server
import logging
import sys
from embed_model import EmbedModel
import argparse


def normal_chat(chatbot, chatlist):
    while 1:
        if len(chatlist) == 0:
            message = input("开始您的对话吧：\n>>> ")
        else:
            message = input()
        response = chatbot.chat(message)
        if response:
            chatlist.append("<<< " + response + "\n>>> ")


def return_vist_chat(chatbot, chatlist):
    while 1:
        response = chatbot.return_visit()
        if response:
            chatlist.append("<<< " + response + "\n>>> ")
        time.sleep(2)


def conversation(chatbot):
    chatlist = []
    chatlist_len = 0
    threading.Thread(target=normal_chat, args=(chatbot, chatlist)).start()
    threading.Thread(target=return_vist_chat, args=(chatbot, chatlist)).start()
    while 1:
        current_chatlist_len = len(chatlist)
        if current_chatlist_len > chatlist_len:
            for message in chatlist[chatlist_len:]:
                print(message, end="")
            chatlist_len = current_chatlist_len

def parse_args():
    parser = argparse.ArgumentParser(description="chatbot")
    parser.add_argument("--embed-model", required=True, default="/mnt/data/wangyesong01/gte-Qwen2-1.5B-instruct")
    parser.add_argument("--vllm-port", required=True, type=int, default=8080)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()

    try:
        server, model_type = get_vllm_server(port=args.vllm_port)
    except Exception as e:
        logging.error(e)
        sys.exit(1)
    chatbot = VllmChatBot(
        server=server,
        model_type=model_type,
        embed_model=EmbedModel(args.embed_model),
        knowledge_bank=[
            "补习班一般凌晨两点上课，上到第二天五点",
            "补习班收费很贵，要10000元一节课",
            "我们班只有一个老师，姓韩。"
        ]
    )

    conversation(chatbot)
