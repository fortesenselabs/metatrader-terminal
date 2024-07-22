#  This file is was adpted from OctoBot (https://github.com/Drakkar-Software/OctoBot)
import async_channel.channels as channel_instances
import async_channel.util as channel_creator
from utils import Logger

import octobot_commons.enums as enums
import octobot_commons.logging as logging

import octobot_evaluators.octobot_channel_consumer as evaluator_channel_consumer

import octobot_services.octobot_channel_consumer as service_channel_consumer

import octobot_trading.api as trading_api
import octobot_trading.octobot_channel_consumer as trading_channel_consumer

import octobot.channels as octobot_channel


class ServerChannelGlobalConsumer:

    def __init__(self, octobot):
        self.octobot = octobot
        self.logger = Logger(name=self.__class__.__name__)

        # the list of server channel consumers
        self.server_channel_consumers = []

        # the OctoBot Channel instance
        self.octobot_channel = None

    async def initialize(self):
        # Creates OctoBot Channel
        self.octobot_channel: octobot_channel.OctoBotChannel = (
            await channel_creator.create_channel_instance(
                octobot_channel.OctoBotChannel,
                channel_instances.set_chan_at_id,
                is_synchronized=True,
                bot_id=self.octobot.bot_id,
            )
        )

        # Initialize global consumer
        self.server_channel_consumers.append(
            await self.octobot_channel.new_consumer(
                self.octobot_channel_callback, bot_id=self.octobot.bot_id
            )
        )

        # Initialize trading consumer
        self.server_channel_consumers.append(
            await self.octobot_channel.new_consumer(
                trading_channel_consumer.octobot_channel_callback,
                bot_id=self.octobot.bot_id,
                action=[
                    action.value
                    for action in trading_channel_consumer.OctoBotChannelTradingActions
                ],
            )
        )

        # Initialize evaluator consumer
        self.server_channel_consumers.append(
            await self.octobot_channel.new_consumer(
                evaluator_channel_consumer.octobot_channel_callback,
                bot_id=self.octobot.bot_id,
                action=[
                    action.value
                    for action in evaluator_channel_consumer.OctoBotChannelEvaluatorActions
                ],
            )
        )

        # Initialize service consumer
        self.server_channel_consumers.append(
            await self.octobot_channel.new_consumer(
                service_channel_consumer.octobot_channel_callback,
                bot_id=self.octobot.bot_id,
                action=[
                    action.value
                    for action in service_channel_consumer.OctoBotChannelServiceActions
                ],
            )
        )

    async def octobot_channel_callback(self, bot_id, subject, action, data) -> None:
        """
        OctoBot channel consumer callback
        :param bot_id: the callback bot id
        :param subject: the callback subject
        :param action: the callback action
        :param data: the callback data
        """
        if subject == enums.OctoBotChannelSubjects.NOTIFICATION.value:
            if (
                action
                == trading_channel_consumer.OctoBotChannelTradingActions.EXCHANGE.value
            ):
                if (
                    trading_channel_consumer.OctoBotChannelTradingDataKeys.EXCHANGE_ID.value
                    in data
                ):
                    exchange_id = data[
                        trading_channel_consumer.OctoBotChannelTradingDataKeys.EXCHANGE_ID.value
                    ]
                    self.octobot.exchange_producer.register_created_exchange_id(
                        exchange_id
                    )
                    await self.logger.init_exchange_chan_logger(exchange_id)
                    exchange_configuration = (
                        trading_api.get_exchange_configuration_from_exchange_id(
                            exchange_id
                        )
                    )
                    await self.octobot.evaluator_producer.create_evaluators(
                        exchange_configuration
                    )
                    # If an exchange is created before interface producer is done, it will be registered via
                    # self.octobot.interface_producer directly on creation
                    await self.octobot.interface_producer.register_exchange(exchange_id)
            elif (
                action
                == evaluator_channel_consumer.OctoBotChannelEvaluatorActions.EVALUATOR.value
            ):
                if not self.octobot.service_feed_producer.started:
                    # Start service feeds now that evaluators registered their feed requirements
                    await self.octobot.service_feed_producer.start_feeds()
            elif (
                action
                == service_channel_consumer.OctoBotChannelServiceActions.INTERFACE.value
            ):
                await self.octobot.interface_producer.register_interface(
                    data[
                        service_channel_consumer.OctoBotChannelServiceDataKeys.INSTANCE.value
                    ]
                )
            elif (
                action
                == service_channel_consumer.OctoBotChannelServiceActions.NOTIFICATION.value
            ):
                await self.octobot.interface_producer.register_notifier(
                    data[
                        service_channel_consumer.OctoBotChannelServiceDataKeys.INSTANCE.value
                    ]
                )
            elif (
                action
                == service_channel_consumer.OctoBotChannelServiceActions.SERVICE_FEED.value
            ):
                await self.octobot.service_feed_producer.register_service_feed(
                    data[
                        service_channel_consumer.OctoBotChannelServiceDataKeys.INSTANCE.value
                    ]
                )

    async def stop(self) -> None:
        """
        Remove all OctoBot Channel consumers
        """
        for consumer in self.server_channel_consumers:
            await self.octobot_channel.remove_consumer(consumer)
