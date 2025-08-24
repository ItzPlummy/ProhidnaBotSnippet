import asyncio
from typing import Dict, Callable

from aiohttp import ClientSession, ClientResponse, ClientConnectorError

from app.bot.classes.attributed_dict import AttributedDict


class RequestManager:
    def __init__(
            self,
            base_url: str,
            api_key: str,
            api_version: str | None = None,
    ):
        self.base_url = base_url
        self.base_header: Dict[str, str] = {"X-API-Key": api_key}
        self.api_version = api_version

    @staticmethod
    def apply_resend(
            func: Callable,
            cycles: int = 3
    ) -> Callable:
        async def wrapper(
                *args,
                **kwargs
        ) -> AttributedDict:
            connection_error: ClientConnectorError | None = None

            for _ in range(cycles):
                try:
                    return await func(*args, **kwargs)
                except ClientConnectorError as error:
                    connection_error = error
                    await asyncio.sleep(1)

            raise connection_error

        return wrapper

    @apply_resend
    async def get(
            self,
            path: str,
            **kwargs
    ) -> AttributedDict:
        headers = self.base_header.copy()
        headers.update(kwargs.get("headers", {}))

        client_session = ClientSession(
            self.base_url,
            headers=headers
        )

        async with client_session as session:
            request = session.get(
                f"{self.api_version}/{path}",
                **kwargs
            )

            async with request as response:
                return await self.construct_response(response)

    @apply_resend
    async def post(
            self,
            path: str,
            **kwargs
    ) -> AttributedDict:
        headers = self.base_header.copy()
        headers.update(kwargs.get("headers", {}))

        client_session = ClientSession(
            self.base_url,
            headers=headers
        )

        async with client_session as session:
            request = session.put(
                f"{self.api_version}/{path}",
                **kwargs
            )

            async with request as response:
                return await self.construct_response(response)

    @apply_resend
    async def put(
            self,
            path: str,
            **kwargs
    ) -> AttributedDict:
        headers = self.base_header.copy()
        headers.update(kwargs.get("headers", {}))

        client_session = ClientSession(
            self.base_url,
            headers=headers
        )

        async with client_session as session:
            request = session.put(
                f"{self.api_version}/{path}",
                **kwargs
            )

            async with request as response:
                return await self.construct_response(response, False)

    @apply_resend
    async def delete(
            self,
            path: str,
            **kwargs
    ) -> AttributedDict:
        headers = self.base_header.copy()
        headers.update(kwargs.get("headers", {}))

        client_session = ClientSession(
            self.base_url,
            headers=headers
        )

        async with client_session as session:
            request = session.delete(
                f"{self.api_version}/{path}",
                **kwargs
            )

            async with request as response:
                return await self.construct_response(response, False)

    @staticmethod
    async def construct_response(
            response: ClientResponse,
            insert_json: bool = True
    ) -> AttributedDict:
        json_response: dict

        if insert_json:
            json_response = await response.json()
        else:
            json_response = {}

        json_response.update(
            {
                "status_code": response.status
            }
        )

        return AttributedDict(json_response)
