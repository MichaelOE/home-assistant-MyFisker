# import asyncio
import json
import logging

import aiohttp

from .const import (
    API_TIMEOUT,
    TOKEN_URL,
    WSS_URL_EU,
    WSS_URL_US,
    CAR_SETTINGS,
    DIGITAL_TWIN,
    PROFILES,
)

_LOGGER = logging.getLogger(__name__)

headers = {"User-Agent": "MOBILE 1.0.0.0"}

HasAUTH = False
HasVIN = False


class MyFiskerAPI:
    """Handle connection towards Fisker API servers."""

    # Global variable to store the WebSocket connection
    global_websocket = None

    vin = ""

    def __init__(self, username: str, password: str, region: str):
        _LOGGER.debug("MyFiskerAPI init")
        self._username = username
        self._password = password
        self._region = region

        self._token = ""
        self._timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        self.data = {}

    # async def WebsocketHandler(self):
    #     global global_websocket
    #     global_websocket = aiohttp.ClientSession()

    #     wssUrl = self.__GetRegionURL()

    #     async with global_websocket as session:
    #         async with session.ws_connect(wssUrl, headers=headers) as ws:
    #             await ws.send_str(json.dumps(self.GenerateVerifyRequest()))
    #             while True:
    #                 response = await ws.receive_str()

    async def GetAuthTokenAsync(self):
        """Get the Authentification token from Fisker, is used towards the WebSocket connection."""

        params = {"username": self._username, "password": self._password}
        async with aiohttp.ClientSession() as session, session.post(
            TOKEN_URL, data=params
        ) as response:
            data = await response.json()

            # Check if a key exists
            if "accessToken" in data:
                retVal = data["accessToken"]
            else:
                retVal = data["message"]

            self._token = retVal
            return self._token

    async def tokenReturn(self):
        return self._token

    def GetCarSettings(self):
        try:
            data = json.loads(self.data[CAR_SETTINGS])
            return data
        except NameError:
            _LOGGER.warning("Self.data['car_settings'] is not available")
            return None

    async def GetDigitalTwin(self):
        self.data[DIGITAL_TWIN] = self.flatten_json(
            self.ParseDigitalTwinResponse(
                await self.__GetWebsocketResponse(DIGITAL_TWIN)
            )
        )
        return self.data[DIGITAL_TWIN]

    async def GetProfiles(self):
        self.data[PROFILES] = self.ParseProfilesResponse(
            await self.__GetWebsocketResponse(PROFILES)
        )
        return self.data[PROFILES]

    def ParseDigitalTwinResponse(self, jsonMsg):
        # _LOGGER.debug('Start ParseDigitalTwinResponse()')
        # Parse the JSON response into a Python dictionary
        data = json.loads(jsonMsg)
        # print (data)
        if data["handler"] != DIGITAL_TWIN:
            _LOGGER.debug("ParseDigitalTwinResponse: Wrong answer from websocket")
            _LOGGER.debug(data)
            return "Wrong answer from websocket"

        # Now you can access the items in the JSON response as you would with a Python dictionary
        digital_twin = data["data"]

        # Use the jsonpath expression to find the value in the data
        _LOGGER.debug(digital_twin)  # Outputs: value1
        return digital_twin

    def GenerateVerifyRequest(self):
        # _LOGGER.debug('Start GenerateVerifyRequest()')
        data = {}
        messageData = {}

        # token = self.GetAuthToken(username, password)
        token = self._token

        data["token"] = token
        messageData["data"] = data
        messageData["handler"] = "verify"
        # print (messageData)
        return messageData

    def ParseVerifyResponse(self, jsonMsg):
        # Parse the JSON response into a Python dictionary
        data = json.loads(jsonMsg)

        if data["handler"] != "verify":
            return "Wrong answer from websocket"

        # Now you can access the items in the JSON response as you would with a Python dictionary
        item1 = data["data"]["authenticated"]

        if item1 != "true":
            return "Not authenticated"

        result = item1
        _LOGGER.debug(result)  # Outputs: value1
        return True

    def GenerateProfilesRequest(self):
        # _LOGGER.debug('Start GenerateProfilesRequest()')
        messageData = {}

        messageData["handler"] = PROFILES
        # print (messageData)
        return messageData

    def DigitalTwinRequest(self, vin):
        # _LOGGER.debug('Start DigitalTwinRequest()')
        data = {}
        messageData = {}
        data["vin"] = self.vin
        messageData["data"] = data
        messageData["handler"] = DIGITAL_TWIN
        return messageData

    def ParseProfilesResponse(self, jsonMsg):
        # _LOGGER.debug('Start ParseProfilesResponse()')
        # Parse the JSON response into a Python dictionary
        data = json.loads(jsonMsg)
        # print (data)
        if data["handler"] != PROFILES:
            _LOGGER.debug("ParseProfilesResponse: Wrong answer from websocket")
            _LOGGER.debug(data)
            return "Wrong answer from websocket"

        # Now you can access the items in the JSON response as you would with a Python dictionary
        item1 = data["data"][0]["vin"]

        # Use the jsonpath expression to find the value in the data
        result = item1
        return result

    async def SendCommandRequest(self, command):
        # _LOGGER.debug('Start SendCommandRequest()')
        data = {}
        messageData = {}
        data["vin"] = self.vin
        data["command"] = command
        messageData["data"] = data
        messageData["handler"] = "remote_command"
        return await self.__SendWebsocketRequest(messageData)

    def __GetRegionURL(self):
        match self._region:
            case "EU":
                return WSS_URL_EU
            case "US":
                return WSS_URL_US
            case _:
                return WSS_URL_US

    async def __GetWebsocketResponse(self, responseToReturn: str):
        HasAUTH = False
        HasVIN = HasAUTH

        wssUrl = self.__GetRegionURL()

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(wssUrl, headers=headers) as ws:
                await ws.send_str(json.dumps(self.GenerateVerifyRequest()))
                while True:
                    response = await ws.receive_str()
                    handler = json.loads(response)["handler"]

                    if handler == CAR_SETTINGS:
                        self.data[CAR_SETTINGS] = response

                    if handler == responseToReturn:
                        try:
                            await ws.close()
                        except Exception as e:
                            _LOGGER.debug(
                                f"Error occurred while closing WebSocket: {e}"
                            )
                        return response

                    if HasAUTH is not True:
                        if handler == "verify":
                            HasAUTH = (
                                json.loads(response)["data"]["authenticated"] is True
                            )
                            # Send a message
                            # _LOGGER.debug(f"Sending 'GenerateProfilesRequest'")
                            await ws.send_str(
                                json.dumps(self.GenerateProfilesRequest())
                            )

                    if HasAUTH is True and HasVIN is not True:
                        if handler == PROFILES:
                            self.vin = self.ParseProfilesResponse(response)
                            # print (f"vin = {vin}")
                            if self.vin != "":
                                self.HasVIN = True
                                # Send a message
                                _LOGGER.debug(
                                    f"Auth & VIN ok - Sending 'DigitalTwinRequest' to vin={self.vin}"
                                )
                                await ws.send_str(
                                    json.dumps(self.DigitalTwinRequest(self.vin))
                                )

                    if HasAUTH is True and HasVIN is True:
                        # _LOGGER.debug(f"Received message: {message}")
                        if handler == responseToReturn:
                            # self.ParseDigitalTwinResponse(response)
                            _LOGGER.error(response)
                            try:
                                await ws.close()
                            except Exception as e:
                                _LOGGER.error(
                                    f"Error occurred while closing WebSocket: {e}"
                                )

                            return response

    async def __SendWebsocketRequest(self, commandToSend: str):
        HasAUTH = False
        wssUrl = self.__GetRegionURL()

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(wssUrl, headers=headers) as ws:
                await ws.send_str(json.dumps(self.GenerateVerifyRequest()))
                while True:
                    response = await ws.receive_str()
                    handler = json.loads(response)["handler"]

                    if handler in (DIGITAL_TWIN, CAR_SETTINGS):
                        try:
                            await ws.close()
                        except Exception as e:
                            _LOGGER.debug(
                                f"Error occurred while closing WebSocket: {e}"
                            )
                        return response

                    if HasAUTH is not True:
                        if handler == "verify":
                            HasAUTH = (
                                json.loads(response)["data"]["authenticated"] is True
                            )
                            # Send a message
                            # _LOGGER.debug(f"Sending 'GenerateProfilesRequest'")
                            await ws.send_str(json.dumps(commandToSend))

    def flatten_json(self, jsonIn):
        out = {}

        def flatten(x, name=""):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + "_")
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + "_")
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(jsonIn)
        return out


class MyFiskerApiError(Exception):
    """Base exception for all MyFisker API errors"""


class AuthenticationError(MyFiskerApiError):
    """Authenatication failed"""


class RequestError(MyFiskerApiError):
    """Failed to get the results from the API"""

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code


class RequestConnectionError(MyFiskerApiError):
    """Failed to make the request to the API"""


class RequestTimeoutError(MyFiskerApiError):
    """Failed to get the results from the API"""


class RequestRetryError(MyFiskerApiError):
    """Retries too many times"""


class RequestDataError(MyFiskerApiError):
    """Data is not valid"""
