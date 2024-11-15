from openai import OpenAI
import time
import subprocess
import logging
import os


def warmup(client, prompt, n):
    for i in range(n):
        logging.info(f'第{i}轮热身')
        _ = client.chat.completions.create(
            model=os.getenv("MODEL_ALIAS", "LLM"),
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )


def run_vllm_server():
    p = subprocess.Popen(
        [
            "sh",
            "run_vllm.sh",
        ],
    )


def get_vllm_server(probe_gap=5, port=8080):
    client = OpenAI(
        base_url=f"http://localhost:{os.getenv('VLLM_SERVER_PORT', port)}/v1",
        api_key="EMPTY",
    )

    model_type = client.models.list().data[0].id
    print(f'model_type: {model_type}')

    # probe readiness
    i = 0
    probe_query = "Are you ready?!"
    while True:
        try:
            completion = client.chat.completions.create(
                model=model_type,
                messages=[
                    {"role": "user", "content": probe_query}
                ]
            )
            return client, model_type
        except Exception as ex:
            logging.info(str(ex))
            i += 1
            logging.info(f"Probe readiness: try {i}")
            time.sleep(probe_gap)
