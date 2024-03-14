# Universal API Service

## Overview

使用 discord 的机器人，封装 midjourney 的生成服务。

核心思路: 通过discord bot api, 下发`/imagine`命令

API服务器, 通过API发生命令, 然后通过机器人来触发响应

## Links

- 参考开源方案：https://github.com/yokonsan/midjourney-api
-

参考文档: https://mp.weixin.qq.com/s?__biz=Mzg4MjkzMzc1Mg==&mid=2247484029&idx=1&sn=d3c458bba9459f19f05d13ab23f5f67e&token=79614426&lang=zh_CN#rd

- 社区项目: https://discord.com/developers/docs/topics/community-resources#libraries
- [https://github.com/python-discord/bot](https://github.com/python-discord/bot)
  -[Midjourney params list](https://docs.midjourney.com/docs/parameter-list)

## 工作原理

通过API实现触发`/imagine`命令, 然后通过机器人来触发响应。

- API服务器接收到`/imagine`命令后, 向midjourney-api发起请求, midjourney-api生成图片并返回给API服务器
- 这等同于用户在discord中输入`/imagine`命令;
- discord机器人监听channel中的事件消息
- 解析任务指令后, 生成payload描述文本,组装成任务发送到midjourney服务器;
- midjourney将参数请求放入队列
- midjourney从队列中取出任务, 并进行生成,
- 生成完毕后, 由discord机器人发送到频道中
- 操作过程需要记录到数据库和日志;

## TL;DR

- create server
- create channel
- create bot
- invite midjourney bot to channel
    - go to midjourney server and find the midjourney bot
    - left-click on the bot and select `add app` to your own server <server_name>
    - and then go to your own server <server_name>

#

同一个库
request_id -> trriger_id
task_id
sub_task c重新生成

存纹理风格, 创意纹理

## 请求间隔

应该是每三秒限制一次


