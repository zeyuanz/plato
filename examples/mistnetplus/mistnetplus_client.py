import logging
from dataclasses import dataclass

from plato.config import Config
from plato.clients import simple

from mistnetplus import DataSource, Trainer

@dataclass
class Report:
    """Client report sent to the MistNet federated learning server."""
    num_samples: int
    payload_length: int

# copy from split_learning and update the model aggregation
class Client(simple.Client):
    def __init__(self, model=None, datasource=None, trainer=None):
        super().__init__()

        self.model_received = False
        self.gradient_received = False
    
    def load_payload(self, server_payload):
        """Loading the server model onto this client."""
        if self.model_received == True and self.gradient_received == True:
            self.model_received = False
            self.gradient_received = False

        if self.model_received == False:
            self.model_received = True
            self.algorithm.load_weights(server_payload)
        elif self.gradient_received == False:
            self.gradient_received = True
            self.algorithm.receive_gradients(server_payload)
            
    async def train(self):
        """A split learning client only uses the first several layers in a forward pass."""
        logging.info("Training on client #%d", self.client_id)
        assert not Config().clients.do_test

        if self.gradient_received == False:
            # Perform a forward pass till the cut layer in the model
            features = self.algorithm.extract_features(
                self.trainset, self.sampler,
                Config().algorithm.cut_layer)

            # Generate a report for the server, performing model testing if applicable
            return Report(self.sampler.trainset_size(),
                          len(features)), features
        else:
            # Perform a complete training with gradients received
            config = Config().trainer._asdict()
            self.algorithm.complete_train(config, self.trainset, self.sampler,
                                          Config().algorithm.cut_layer)
            weights = self.algorithm.extract_weights()
            # Generate a report, signal the end of train
            train_status = "train done"
            return Report(self.sampler.trainset_size(), 0), weights

def main():
    """A Plato federated learning training session using a custom model. """
    model = nn.Sequential(
        nn.Linear(28 * 28, 128),
        nn.ReLU(),
        nn.Linear(128, 128),
        nn.ReLU(),
        nn.Linear(128, 10),
    )

    server = fedReIdServer(model=model)
    server.run()


if __name__ == "__main__":
    main()
