## 火焰

```json

[
    {
        "id": 1,
        "name": "火焰",
        "image": "https://static.molook.cn/texture/xhcyw2_68942587433767268989976553721136425105_Photo_of_a_tiger__8537f33a-522d-4777-88e5-d9f55f2f2eb4_top_left_1_.png",
        "prompt": [
            "Photo of {subject} sitting on fire."
        ],
        "instructions": null,
        "tags": null,
        "parameters": null,
        "description": "火焰背景, 切换主体",
        "created_at": "2024-03-14 21:03:48",
        "updated_at": "2024-03-14 21:03:50"
    }
]
```

```mysql
INSERT INTO moway_look.pattern_preset (id, name, image, prompt, instructions, tags, parameters, description, created_at,
                                       updated_at)
VALUES (1, '火焰',
        'https://static.molook.cn/texture/xhcyw2_68942587433767268989976553721136425105_Photo_of_a_tiger__8537f33a-522d-4777-88e5-d9f55f2f2eb4_top_left_1_.png',
        '["Photo of {subject} sitting on fire."]', null, null, null, '火焰背景, 切换主体', '2024-03-14 21:03:48',
        '2024-03-14 21:03:50');

```