import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import pandas as pd
import torchvision
from torchvision import *
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import matplotlib.image as img
import matplotlib.pyplot as plt
import time
import copy
import os
import cv2

import warnings
warnings.filterwarnings("ignore")

from google.colab import drive
drive.mount('/content/drive')

torch.cuda.is_available()

!nvidia-smi

img_orig = '/content/drive/MyDrive/Data/image/'
labels = pd.read_csv('/content/drive/MyDrive/Data/label.csv')
labels.label.unique()
labels.head()

fig,ax = plt.subplots(1,5,figsize = (15,3))

for i,idx in enumerate(labels[labels['label'] == '短袖']['item_id'][-5:]):
    path = os.path.join(img_orig,idx)
    ax[i].imshow(img.imread(path))

labels.label = labels.label.replace('短袖', 0)
labels.label = labels.label.replace('衣裙', 1)
labels.label = labels.label.replace('裙子', 2)
labels.label = labels.label.replace('毛衣', 3)
labels.label = labels.label.replace('T恤', 4)
labels.label = labels.label.replace('衬衫', 5)
labels.label = labels.label.replace('大衣', 6)
labels.label = labels.label.replace('西服', 7)
labels.label = labels.label.replace('卫衣', 8)
labels.label = labels.label.replace('风衣', 9)
labels.label = labels.label.replace('上衣', 10)
labels.label = labels.label.replace('裤', 11)
labels.label = labels.label.replace('外套', 12)
labels.label = labels.label.replace('羽绒服', 13)
labels.label = labels.label.replace('文胸', 14)
labels.label = labels.label.replace('帽衫', 15)
labels.label = labels.label.replace('帽子', 16)
labels.label = labels.label.replace('衣服', 17)

import matplotlib.pyplot as plt

def imshow(image, ax=None, title=None, normalize=True):
    if ax is None:
        fig, ax = plt.subplots()
    image = image.numpy().transpose((1, 2, 0))

    if normalize:
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        image = std * image + mean
        image = np.clip(image, 0, 1)

    ax.imshow(image)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.set_xticklabels('')
    ax.set_yticklabels('')

    return ax

class CactiDataset(Dataset):
    def __init__(self, data, path, transform = None):
        super().__init__()
        self.data = data.values
        self.path = path
        self.transform = transform
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self,index):
        img_name,label = self.data[index]
        img_path = os.path.join(self.path, img_name)
        image = Image.open(img_path).convert('RGB')
        
        if self.transform is not None:
            image = self.transform(image)
        return image, label

train_transform = transforms.Compose([transforms.Resize((224,224)),
                                      transforms.ToTensor(),
                                      transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

valid_transform = transforms.Compose([transforms.Resize((224,224)),
                                      transforms.ToTensor(),
                                      transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

from sklearn.model_selection import train_test_split

train, valid = train_test_split(labels, stratify=labels.label, test_size=0.2)

train_data = CactiDataset(train, img_orig, train_transform)
valid_data = CactiDataset(valid, img_orig, valid_transform)

num_epochs = 15
num_classes = 18
batch_size = 25
learning_rate = 0.001

train_loader = DataLoader(dataset = train_data, batch_size = batch_size, shuffle=True, num_workers=0)
valid_loader = DataLoader(dataset = valid_data, batch_size = batch_size, shuffle=True, num_workers=0)

trainimages, trainlabels = next(iter(train_loader))

fig, axes = plt.subplots(figsize=(12, 12), ncols=5)
print('training images')
for i in range(5):
    axe1 = axes[i] 
    imshow(trainimages[i], ax=axe1, normalize=False)

print(trainimages[0].size())

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
model = models.efficientnet_b0(pretrained=True)
model

num_epochs = 15
num_classes = 18
batch_size = 25
learning_rate = 0.001

model = model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(),lr = learning_rate)

# Commented out IPython magic to ensure Python compatibility.
# %%time
# from tqdm import tqdm
# 
# # keeping-track-of-losses 
# train_losses = []
# valid_losses = []
# train_acc = []
# valid_acc = []
# 
# for epoch in tqdm(range(1, num_epochs + 1)):
#     # keep-track-of-training-and-validation-loss
#     train_loss = 0.0
#     valid_loss = 0.0
#     correct = 0
#     total = 0
#     correct_t = 0
#     total_t = 0
# 
#     # training-the-model
#     model.train()
#     for data, target in tqdm(train_loader):
#         # move-tensors-to-GPU 
#         data = torch.tensor(data).to(device)
#         target = torch.tensor(target).to(device)
#         
#         # clear-the-gradients-of-all-optimized-variables
#         optimizer.zero_grad()
#         # forward-pass: compute-predicted-outputs-by-passing-inputs-to-the-model
#         output = model(data)
#         # calculate-the-batch-loss
#         loss = criterion(output, target)
#         # backward-pass: compute-gradient-of-the-loss-wrt-model-parameters
#         loss.backward()
#         # perform-a-ingle-optimization-step (parameter-update)
#         optimizer.step()
#         # measure accuracy
#         _,pred = torch.max(output, 1)
#         correct += torch.sum(pred==target).item()
#         total += target.size(0)
#         # update-training-loss
#         train_loss += loss.item() * data.size(0)
#         train_acc = 100 * correct / total
# 
#     # validate-the-model
#     model.eval()
#     for data, target in tqdm(valid_loader):
#         
#         data = torch.tensor(data).to(device)
#         target = torch.tensor(target).to(device)
#         
#         output = model(data)
#         
#         loss = criterion(output, target)
#         # measure accuracy
#         _,pred = torch.max(output, 1)
#         correct_t += torch.sum(pred==target).item()
#         total_t += target.size(0)
#         # update-average-validation-loss 
#         valid_loss += loss.item() * data.size(0)
#         valid_acc = 100 * correct_t /total_t
#     # calculate-average-losses
#     train_loss = train_loss/len(train_loader.sampler)
#     valid_loss = valid_loss/len(valid_loader.sampler)
#     train_losses.append(train_loss)
#     valid_losses.append(valid_loss)
#     train_acc.append(train_acc)
#     valid_acc.append(valid_acc)
#         
#     # print-training/validation-statistics 
#     print('Epoch: {} \tTraining Loss: {:.6f} \tValidation Loss: {:.6f}'.format(
#         epoch, train_loss, valid_loss))

model.eval()  # it-disables-dropout
with torch.no_grad():
    correct = 0
    total = 0
    for images, labels in tqdm(valid_loader):
        images = torch.tensor(images).to(device)
        labels = torch.tensor(labels).to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
    print('Test Accuracy of the model: {} %'.format(100 * correct / total))

# Save 
torch.save(model.state_dict(), 'model.ckpt')

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
# %config InlineBackend.figure_format = 'retina'

plt.plot(train_losses, label='Training loss')
plt.plot(valid_losses, label='Validation loss')
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend(frameon=False)
