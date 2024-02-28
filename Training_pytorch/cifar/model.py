from utee import misc
print = misc.logger.info
import torch.nn as nn
from modules.quantization_cpu_np_infer import QConv2d, QLinear
import torch

class CIFAR(nn.Module):
    def __init__(self, args, features, num_classes,logger):
        super(CIFAR, self).__init__()
        assert isinstance(features, nn.Sequential), type(features)
        self.features = features
        self.classifier = nn.Sequential(
            QLinear(8192, 1024, logger=logger,
                    wl_input = args.wl_activate,wl_activate=args.wl_activate,wl_error=args.wl_error,
                    wl_weight=args.wl_weight,inference=args.inference,onoffratio=args.onoffratio,cellBit=args.cellBit,
                    subArray=args.subArray,ADCprecision=args.ADCprecision,vari=args.vari,t=args.t,v=args.v,detect=args.detect,target=args.target, name='FC1_'),
            nn.ReLU(inplace=True),
            QLinear(1024, num_classes, logger=logger,
                    wl_input = args.wl_activate,wl_activate=-1, wl_error=args.wl_error,
                    wl_weight=args.wl_weight,inference=args.inference,onoffratio=args.onoffratio,cellBit=args.cellBit,
                    subArray=args.subArray,ADCprecision=args.ADCprecision,vari=args.vari,t=args.t,v=args.v,detect=args.detect,target=args.target,name='FC2_'))

        print(self.features)
        print(self.classifier)

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

class LeNet(nn.Module):
    def __init__(self, args, features, num_classes,logger):
        super(LeNet, self).__init__()
        assert isinstance(features, nn.Sequential), type(features)
        self.features = features
        self.classifier = nn.Sequential(
            QLinear(1024, 120, logger=logger,
                    wl_input = args.wl_activate,wl_activate=args.wl_activate,wl_error=args.wl_error,
                    wl_weight=args.wl_weight,inference=args.inference,onoffratio=args.onoffratio,cellBit=args.cellBit,
                    subArray=args.subArray,ADCprecision=args.ADCprecision,vari=args.vari,t=args.t,v=args.v,detect=args.detect,target=args.target, name='FC1_'),
            nn.ReLU(),
            QLinear(120, 84, logger=logger,
                    wl_input = args.wl_activate,wl_activate=-1, wl_error=args.wl_error,
                    wl_weight=args.wl_weight,inference=args.inference,onoffratio=args.onoffratio,cellBit=args.cellBit,
                    subArray=args.subArray,ADCprecision=args.ADCprecision,vari=args.vari,t=args.t,v=args.v,detect=args.detect,target=args.target,name='FC2_'),
            nn.ReLU(),
            QLinear(84, num_classes, logger=logger,
                    wl_input = args.wl_activate,wl_activate=-1, wl_error=args.wl_error,
                    wl_weight=args.wl_weight,inference=args.inference,onoffratio=args.onoffratio,cellBit=args.cellBit,
                    subArray=args.subArray,ADCprecision=args.ADCprecision,vari=args.vari,t=args.t,v=args.v,detect=args.detect,target=args.target,name='FC3_')

        )

        print(self.features)
        print(self.classifier)

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


def make_layers(cfg, args, logger ):
    layers = []
    in_channels = 3
    for i, v in enumerate(cfg):
        if v[0] == 'M':
            layers += [nn.MaxPool2d(kernel_size=v[1], stride=v[2])]
        if v[0] == 'A':
            layers += [nn.AvgPool2d(kernel_size=v[1], stride=v[2])]
        if v[0] == 'C':
            out_channels = v[1]
            if v[3] == 'same':
                padding = v[2]//2
            else:
                padding = 0
            conv2d = QConv2d(in_channels, out_channels, kernel_size=v[2], padding=padding,
                             logger=logger,wl_input = args.wl_activate,wl_activate=args.wl_activate,
                             wl_error=args.wl_error,wl_weight= args.wl_weight,inference=args.inference,onoffratio=args.onoffratio,cellBit=args.cellBit,
                             subArray=args.subArray,ADCprecision=args.ADCprecision,vari=args.vari,t=args.t,v=args.v,detect=args.detect,target=args.target,
                             name = 'Conv'+str(i)+'_' )
            if v[4] == "sigmoid":
                non_linearity_activation = nn.Sigmoid()
            else: 
                non_linearity_activation =  nn.ReLU()
            layers += [conv2d, non_linearity_activation]
            in_channels = out_channels
    return nn.Sequential(*layers)


# Args in order
# 0 -> Type 
# 1 -> kernel size / output channels 
# 2 -> padding / kernel size
# 3 -> symmetric padding 
# 4 -> stride
# 5 -> activation

cfg_list = {
    'cifar10': [('C', 128, 3, 'same', 2.0),
                ('C', 128, 3, 'same', 16.0),
                ('M', 2, 2),
                ('C', 256, 3, 'same', 16.0),
                ('C', 256, 3, 'same', 16.0),
                ('M', 2, 2),
                ('C', 512, 3, 'same', 16.0),
                ('C', 512, 3, 'same', 32.0),
                ('M', 2, 2)],

    'lenet5': [
        ('C', 6, 5, 'same', 2.0),  # Convolutional layer with 6 filters, kernel size 5x5
        ('A', 2, 2),                # Max pooling layer with kernel size 2x2 and stride 2
        ('C', 16, 5, 'same', 1.0),  # Convolutional layer with 16 filters, kernel size 5x5
        ('A', 2, 2)                 # Max pooling layer with kernel size 2x2 and stride 2
    ]
}

def cifar10( args, logger, pretrained=None):
    cfg = cfg_list['cifar10']
    layers = make_layers(cfg, args,logger)
    model = CIFAR(args,layers, num_classes=10,logger = logger)
    if pretrained is not None:
        model.load_state_dict(torch.load(pretrained))
    return model

def lenet5(args, logger, pretrained=None):
    cfg = cfg_list['lenet5']
    layers = make_layers(cfg, args,logger)
    model = LeNet(args,layers, num_classes=10,logger = logger)
    if pretrained is not None:
        model.load_state_dict(torch.load(pretrained))
    return model