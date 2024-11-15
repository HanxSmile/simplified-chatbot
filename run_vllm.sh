python -m vllm.entrypoints.openai.api_server \
    --host 0.0.0.0 --port 8080  \
    --served-model-name Llama-3.2-3B-Instruct  \
    --model /mnt/data/hanxiao/models/nlp/Llama-3.2-3B-Instruct  \
    --trust-remote-code --max-num-batched-tokens 16384 --max-model-len 16384 \
    --gpu-memory-utilization 0.9 --tokenizer-mode auto --tensor-parallel-size 1 --dtype auto