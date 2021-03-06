import os

import shutil

import torch
import torch.nn as nn

from torch.autograd import Variable




RESULTS_PATH = 'results/'
WEIGHTS_PATH = 'weights/2nd/'


def save_weights(model, epoch, loss, err):
    weights_fname = 'weights-%d-%.3f-%.3f.pth' % (epoch, loss, err)
    weights_fpath = os.path.join(WEIGHTS_PATH, weights_fname)
    torch.save({
            'startEpoch': epoch,
            'loss':loss,
            'error': err,
            'state_dict': model.state_dict()
        }, weights_fpath)
    shutil.copyfile(weights_fpath, WEIGHTS_PATH+'latest.th')

def load_weights(model, fpath):
    print("loading weights '{}'".format(fpath))
    weights = torch.load(fpath)
    startEpoch = weights['startEpoch']
    model.load_state_dict(weights['state_dict'])
    print("loaded weights (lastEpoch {}, loss {}, error {})"
          .format(startEpoch-1, weights['loss'], weights['error']))
    return startEpoch

def get_predictions(output_batch):
    bs,c,h,w = output_batch.size()
    tensor = output_batch.data
    values, indices = tensor.cpu().max(1)
    indices = indices.view(bs,h,w)
    return indices

def error(preds, targets):
    assert preds.size() == targets.size()
    bs,h,w = preds.size()
    n_pixels = bs*h*w
    #print(n_pixels)
    incorrect = preds.ne(targets).cpu().sum()
    #print(incorrect)
    err = incorrect.numpy() / n_pixels
    return round(err,5)

def train(model, trn_loader, optimizer, criterion, epoch):
    model.train()
    trn_loss = 0
    trn_error = 0
    for idx, data in enumerate(trn_loader):
        inputs = Variable(data[0].cuda())
        targets = Variable(data[1].cuda())

        optimizer.zero_grad()
        output = model(inputs)
        loss = criterion(output, targets)
        loss.backward()
        optimizer.step()

        trn_loss += loss.data[0]
        pred = get_predictions(output)
        trn_error += error(pred, targets.data.cpu())

    trn_loss /= len(trn_loader)
    trn_error /= len(trn_loader)
    return trn_loss, trn_error

def test(model, test_loader):
    torch.cuda.set_device(0)
    model.eval()
    model=model.cuda()
    dataFile = "/home/yachao-li/Downloads/pycharm/lists/100k/drivable/test_images.txt"
    f = open(dataFile, "r")
    data1 = f.readlines()

    for i,data in enumerate(test_loader):

        data = Variable(data, volatile=False).cuda()
        data =data.cuda()
        output = model(data)

        print(i)
        torch.save(output, "/home/yachao-li/Downloads/results/" + data1[i][17:-5] + "_drivable_id.png")

    f.close()

def adjust_learning_rate(lr, decay, optimizer, cur_epoch, n_epochs):
    """Sets the learning rate to the initially
        configured `lr` decayed by `decay` every `n_epochs`"""
    new_lr = lr * (decay ** (cur_epoch // n_epochs))
    for param_group in optimizer.param_groups:
        param_group['lr'] = new_lr

def weights_init(m):
    if isinstance(m, nn.Conv2d):
        nn.init.kaiming_uniform(m.weight)
        m.bias.data.zero_()

def predict(model, input_loader, n_batches=1):
    input_loader.batch_size = 1
    predictions = []
    model.eval()
    for input, target in input_loader:
        data = Variable(input.cuda(), volatile=True)
        label = Variable(target.cuda())
        output = model(data)
        pred = get_predictions(output)
        predictions.append([input,target,pred])
    return predictions

