# API文档

# generate

## API

description:

```http

POST /generate
Content-Type: Application/json

{
    "prompt": "提示词",
    
}
```

## Request Samples

```json
{
    "prompt": "提示词",
    "style": "纹理"
}
```

### Python

```python

```

## Response Samples

### 200

```json


```

### 400

```
```

### 405

```json

{
    "code": 0,
    "message": "405: Method Not Allowed"
}
```

### 500

# ws

```http 
ws /ws/trigger_id
```

# 队列

队列中信息为

```json
{
    "config": {
        "batch_size": 4
    },
    "requestId": "",
    "subTaskId": "",
    "taskId": "",
    "taskType": "TEXTURE",
    "mqParamsId": "",
    "textrue": {
        "prompt": "",
        "tags": [
            ""
        ],
        "styleId": "",
        "aspect": ""
    }
}
```

结果队列必须参数

```json
{
    "data": {
        "images": [],
        "requestId": "",
        "subTaskId": "",
        "taskId": "",
        "mqParamsId": ""
    }
    "code": ""
}

```
