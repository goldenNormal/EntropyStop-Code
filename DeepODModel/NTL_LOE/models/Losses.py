
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

class DCL(nn.Module):
    def __init__(self,temperature=0.1):
        super(DCL, self).__init__()
        self.temp = temperature
    def forward(self,z,eval=False):
        z = F.normalize(z, p=2, dim=-1)
        z_ori = z[:, 0]  # n,z
        z_trans = z[:, 1:]  # n,k-1, z
        batch_size, num_trans, z_dim = z.shape

        sim_matrix = torch.exp(torch.matmul(z, z.permute(0, 2, 1) / self.temp))  # n,k,k
        mask = (torch.ones_like(sim_matrix).to(z) - torch.eye(num_trans).unsqueeze(0).to(z)).bool()
        sim_matrix = sim_matrix.masked_select(mask).view(batch_size, num_trans, -1)
        trans_matrix = sim_matrix[:, 1:].sum(-1)  # n,k-1

        pos_sim = torch.exp(torch.sum(z_trans * z_ori.unsqueeze(1), -1) / self.temp) # n,k-1
        K = num_trans - 1
        scale = 1 / np.abs(K*np.log(1.0 / K))

        loss_tensor = (torch.log(trans_matrix) - torch.log(pos_sim)) * scale

        if eval:
            score = loss_tensor.sum(1)
            return score
        else:
            loss = loss_tensor.sum(1)
            return loss

class EucDCL(nn.Module):
    def __init__(self, temperature=1):
        super().__init__()
        self.temp = temperature

    def forward(self, z, eval=False):

        batch_size, num_trans, z_dim = z.shape
        sim_matrix = -torch.cdist(z,z)

        sim_matrix = torch.exp(sim_matrix / self.temp)  # n,k,k
        mask = (torch.ones_like(sim_matrix).to(z) - torch.eye(num_trans).unsqueeze(0).to(z)).bool()
        sim_matrix = sim_matrix.masked_select(mask).view(batch_size, num_trans, -1)
        sim_matrix = sim_matrix+1e-8
        trans_matrix = sim_matrix[:, 1:].sum(-1)  # n,k-1
        pos_sim = sim_matrix[:, 1:, 0]

        K = num_trans - 1
        scale = 1 / np.abs(K*np.log(1.0 / K))
        score = (-torch.log(pos_sim) + torch.log(trans_matrix)) * scale
        if eval:
            score = score.sum(1)
            return score
        else:
            loss = score.sum(1)
            return loss


class LOEDCL(nn.Module):
    def __init__(self,temperature=0.1):
        super(LOEDCL, self).__init__()
        self.temp = temperature
    def forward(self,z):
        z = F.normalize(z, p=2, dim=-1)
        z_ori = z[:, 0]  # n,z
        z_trans = z[:, 1:]  # n,k-1, z
        batch_size, num_trans, z_dim = z.shape

        sim_matrix = torch.exp(torch.matmul(z, z.permute(0, 2, 1) / self.temp))  # n,k,k
        mask = (torch.ones_like(sim_matrix).to(z) - torch.eye(num_trans).unsqueeze(0).to(z)).bool()
        sim_matrix = sim_matrix.masked_select(mask).view(batch_size, num_trans, -1)
        trans_matrix = sim_matrix[:, 1:].sum(-1)  # n,k-1

        pos_sim = torch.exp(torch.sum(z_trans * z_ori.unsqueeze(1), -1) / self.temp) # n,k-1
        K = num_trans - 1
        scale = 1 / np.abs(np.log(1.0 / K))
        loss_tensor = (torch.log(trans_matrix) - torch.log(pos_sim)) * scale

        loss_n = loss_tensor.mean(1)
        loss_a = -torch.log(1-pos_sim/trans_matrix)*scale
        loss_a = loss_a.mean(1)

        return loss_n,loss_a
