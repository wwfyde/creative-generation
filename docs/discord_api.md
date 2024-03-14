# Discord API

## interaction

```json

{
    "type": 2,
    "application_id": "936929561302675456",
    "guild_id": "1076097007850111017",
    "channel_id": "1076097007850111020",
    "session_id": "ac7b851b907009c24ef4161e57a790c9",
    "data": {
        "version": "1166847114203123795",
        "id": "938956540159881230",
        "name": "imagine",
        "type": 1,
        "options": [
            {
                "type": 3,
                "name": "prompt",
                "value": "hello"
            }
        ],
        "application_command": {
            "id": "938956540159881230",
            "type": 1,
            "application_id": "936929561302675456",
            "version": "1166847114203123795",
            "name": "imagine",
            "description": "Create images with Midjourney",
            "options": [
                {
                    "type": 3,
                    "name": "prompt",
                    "description": "The prompt to imagine",
                    "required": true,
                    "description_localized": "The prompt to imagine",
                    "name_localized": "prompt"
                }
            ],
            "integration_types": [
                0
            ],
            "global_popularity_rank": 1,
            "description_localized": "Create images with Midjourney",
            "name_localized": "imagine"
        },
        "attachments": []
    },
    "nonce": "1211169942624272384",
    "analytics_location": "slash_ui"
}
```

### parameters

https://docs.midjourney.com/docs

```shell
--style raw

--aspect, -a  

# relax mode 当快速生成模式用量完毕后, 采用慢速模式生成
--relax 

# style references 
-sref <url> 
-sref <url1> <url2> ... 

--sw

--stylize
```