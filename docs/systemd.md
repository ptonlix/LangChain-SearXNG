# Linux 设置开机自启动

```
#  /usr/lib/systemd/system/langchain-searxng.service
[Unit]
Description=Langchain-SearXNG
After=network.target

[Service]
Type=simple
ExecStart=/root/miniconda3/envs/LangChain-SearXNG/bin/python -m langchain_searxng

[Install]
WantedBy=multi-user.target
```

```
systemctl enable langchain-searxng.service 开机自启动
systemctl start  langchain-searxng

# 服务启动失败，可通过下面命令查看原因
journalctl -u langchain-searxng -f

```
