import logging
from typing import Optional, Any, Union, Dict, List

import json_repair

from app.domain.external.json_parser import JSONParser

logger = logging.getLogger(__name__)


class RepairJSONParser(JSONParser):

    async def invoke(self, text: str, default_value: Optional[Any] = None) -> \
            Union[Dict, List, Any]:
        logger.info(f'解析json文本：{text}')
        if not text or not text.strip():
            if default_value is not None:
                return default_value
            raise ValueError('json 文本为空，且无默认值')

        return json_repair.repair_json(text, ensure_ascii=False)
