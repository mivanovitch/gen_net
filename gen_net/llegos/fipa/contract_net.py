"""
https://en.m.wikipedia.org/wiki/Contract_Net_Protocol
http://www.fipa.org/specs/fipa00029/SC00029H.pdf
"""

from abc import ABC, abstractmethod
from typing import AsyncIterable, Union

from gen_net.llegos.asyncio import propogate_all
from gen_net.llegos.networks import Field, GenNetwork, Message, NetworkAgent

"""
First, we define our Message types.
"""


class CFP(Message):
    method = "cfp"


class Accept(Message):
    method = "accept"


class Refuse(Message):
    method = "refuse"


class Propose(Message):
    method = "propose"


class AcceptProposal(Message):
    method = "accept_proposal"


class RejectProposal(Message):
    method = "reject_proposal"


class Failure(Message):
    method = "failure"


class InformDone(Message):
    method = "inform_done"


class InformResult(Message):
    method = "inform_result"


class Request(Message):
    method = "request"


class Response(Message):
    method = "response"


"""
Then, onto the agents!
"""


class Participant(NetworkAgent, ABC):
    """
    An abstract base class for a contract net participant, i.e. a contractor meant to
    receive a CFP, respond with a proposal, and then perform the task if their proposal
    was approved.
    """

    receivable_messages = {CFP, RejectProposal, AcceptProposal, Failure}

    @abstractmethod
    async def cfp(self, message: CFP) -> Union[Propose, Refuse]:
        """Receive a call for a proposal and return a proposal or a refusal"""
        ...

    @abstractmethod
    async def accept_proposal(
        self, message: AcceptProposal
    ) -> Union[InformDone, InformResult, Failure]:
        """Receive an accepted proposal and perform the task"""
        ...

    @abstractmethod
    async def reject_proposal(self, message: RejectProposal) -> None:
        """Receive a rejected proposal and process it"""
        ...


class Initiator(NetworkAgent, ABC):
    receivable_messages = {Propose, Refuse, InformDone, InformResult, Failure}

    @abstractmethod
    async def propose(
        self, message: Propose
    ) -> AsyncIterable[Union[AcceptProposal, RejectProposal]]:
        """Receive a proposal and return an acceptance or a rejection"""
        ok = True
        if ok:
            yield AcceptProposal.reply(message)
        else:
            yield RejectProposal.reply(message)

    @abstractmethod
    async def inform_done(self, message: InformDone) -> None:
        """Receive a message that the task is done"""
        ...

    @abstractmethod
    async def inform_result(self, message: InformResult) -> None:
        """Receive a message with the result of the task"""
        yield Response.forward(message, sender=self)

    @abstractmethod
    async def failure(self, message: Failure) -> None:
        """Receive a message that the task failed"""
        ...


Message = Union[CFP, Accept, Refuse, Propose, AcceptProposal, RejectProposal]


class ContractNet(GenNetwork):
    manager: Initiator = Field()
    contractors: list[Participant] = Field(min_items=1)

    def __init__(self, manager: Initiator, contractors: list[Participant], **kwargs):
        super().__init__(
            links=[(manager, "contractor", c) for c in contractors], **kwargs
        )

    async def request(self, message: Request) -> AsyncIterable[Message]:
        messages = [
            CFP.forward(message, sender=self.manager, receiver=c)
            for c in self.contractors
        ]
        async for reply in propogate_all(messages):
            if (yield reply) is StopAsyncIteration:
                break
