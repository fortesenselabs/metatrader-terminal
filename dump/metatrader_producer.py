#  This file is part of OctoBot (https://github.com/Drakkar-Software/OctoBot)

import asyncio
from .channel import ServerChannelProducer


class MetaTraderProducer(ServerChannelProducer):
    def __init__(self, channel, octobot, backtesting, ignore_config=False):
        super().__init__(channel)
        self.octobot = octobot
        self.ignore_config = ignore_config

        self.backtesting = backtesting
        self.exchange_manager_ids = []

        self.to_create_exchanges_count = 0
        self.created_all_exchanges = asyncio.Event()

    async def start(self):
        self.to_create_exchanges_count = 0
        self.created_all_exchanges.clear()
        for exchange_name in trading_api.get_enabled_exchanges_names(
            self.octobot.config
        ):
            await self.create_exchange(exchange_name, self.backtesting)
            self.to_create_exchanges_count += 1

    def register_created_exchange_id(self, exchange_id):
        self.exchange_manager_ids.append(exchange_id)
        if len(self.exchange_manager_ids) == self.to_create_exchanges_count:
            self.created_all_exchanges.set()
            self.logger.debug(f"Exchange(s) created")

    async def stop(self):
        self.logger.debug("Stopping ...")
        for exchange_manager in trading_api.get_exchange_managers_from_exchange_ids(
            self.exchange_manager_ids
        ):
            await trading_api.stop_exchange(exchange_manager)
        self.logger.debug("Stopped")

    async def create_exchange(self, exchange_name, backtesting):
        await self.send(
            bot_id=self.octobot.bot_id,
            subject=common_enums.OctoBotChannelSubjects.CREATION.value,
            action=trading_channel_consumer.OctoBotChannelTradingActions.EXCHANGE.value,
            data={
                trading_channel_consumer.OctoBotChannelTradingDataKeys.TENTACLES_SETUP_CONFIG.value: self.octobot.tentacles_setup_config,
                trading_channel_consumer.OctoBotChannelTradingDataKeys.MATRIX_ID.value: self.octobot.evaluator_producer.matrix_id,
                trading_channel_consumer.OctoBotChannelTradingDataKeys.BACKTESTING.value: backtesting,
                trading_channel_consumer.OctoBotChannelTradingDataKeys.EXCHANGE_CONFIG.value: self.octobot.config,
                trading_channel_consumer.OctoBotChannelTradingDataKeys.EXCHANGE_NAME.value: exchange_name,
            },
        )
