# -*- coding: utf-8 -*-
"""
Created on Fri May  7 17:15:46 2021

@author: HoMingChu
"""

#此部分為dynamic programming 的實作方法

import copy
from random import randint
import time

all_sets = []
g = {} #紀錄距離
p = [] #紀錄路徑
count = 0
matrix = []
subset_k = []


def dp_TSP(size):
    
    global matrix
    global subset_k 
    global all_sets
    global g
    global p
    global count
    
    all_sets = []
    g = {} #紀錄距離
    p = [] #紀錄路徑
    count = 0
    matrix = []
    subset_k = []
    
    matrix_producing(size)
    n = len(matrix)
    for x in range(1, n): #將終點往起點的值放入串列g
        g[x + 1, ()] = matrix[x][0] #()的意思為空集合，可說是已經無值可放入了
    get_minimum(1, subset_k)
    print('\nSolution to TSP: {1, ', end='') #先print出起始值
    
    solution = p.pop() #solution = C<i_to_s>, g(k,[S]-[K])
    print(solution[1][0], end=', ') #solution = g(i,S) = (C<i_to_k>, g(k,[S]-[K]))
    for x in range(n - 2): #少掉第一次和最後一次(都是"1")
        for new_solution in p:
            if tuple(solution[1]) == new_solution[0]:#要得知C<i_to_k>,g(k,[S]-[K])是由哪一個g(k,[S]-[K])所構成
                solution = new_solution #將solution指定成更小的子集
                print(solution[1][0], end=', ') #印出k值
                break
    print('1}') #印出尾數
    #print(count)
    print("Best score calculated by dynamic programming:",g[(1, subset_k)])
    print()
    print()
    return
    


def matrix_producing(size):
    
    global matrix
    global subset_k

    matrix = [[0 for row in range(size)] for column in range(size)]
    for i in range(size):
        for j in range(size):
            if j > i:
                matrix[i][j] = randint(1,30)
                matrix[j][i] = matrix[i][j]
    
    for i in range(1,size+1):
        if i == 1:
            subset_k = []
        else:
            subset_k.append(i)
    subset_k = tuple(subset_k)


def get_minimum(k, a):
    global count
    count += 1
    if (k, a) in g:
        # Already calculated Set g[%d, (%s)]=%d' % (k, str(a), g[k, a]))
        return g[k, a]

    values = []
    all_min = []
    for j in a:
        set_a = copy.deepcopy(list(a)) #a為g(k,[S]-[K])
        set_a.remove(j) #g(i,S) = (C<i_to_k>, g(k,[S]-[K]))之中的C<i_to_k>就是j
        all_min.append([j, tuple(set_a)])#把j值去掉計算更小的子集
        result = get_minimum(j, tuple(set_a))
        values.append(matrix[k-1][j-1] + result) #C<i_to_k> + g(k,[S]-[K])

    # get minimun value from set as optimal solution for
    g[k, a] = min(values)
    p.append(((k, a), all_min[values.index(g[k, a])]))

    return g[k, a]











#此部分為antcolonyoptimizer的實作方法

import numpy as np
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")


class AntColonyOptimizer:
    def __init__(self, ants, evaporation_rate, intensification, alpha=1.0, beta=0.0, beta_evaporation_rate=0,
                 choose_best=.1):
        """
        Ant colony optimizer.  Finds min distance between nodes.
        ants: number of ants
        evaporation_rate: rate at which pheromone evaporates
        intensification: constant added to the best path
        alpha: weighting of pheromone 費洛蒙的濃度加權
        beta: weighting of heuristic (1/distance) beta越大代表距離越遠 為能見度
        beta_evaporation_rate: rate at which beta decays (optional)
        choose_best: probability to choose the best route 
        """
        # 參數
        self.ants = ants
        self.evaporation_rate = evaporation_rate
        self.pheromone_intensification = intensification
        self.heuristic_alpha = alpha
        self.heuristic_beta = beta
        self.beta_evaporation_rate = beta_evaporation_rate
        self.choose_best = choose_best

        # Internal representations
        self.pheromone_matrix = None #濃度矩陣
        self.heuristic_matrix = None #能見度矩陣
        self.probability_matrix = None #可能性矩陣

        self.map = None
        self.set_of_available_nodes = None

        # Internal stats
        self.best_series = []
        self.best = None
        self.fitted = False
        self.best_path = None
        self.fit_time = None

        # Plotting values
        self.stopped_early = False

    def __str__(self):
        string = "Ant Colony Optimizer"
        
        if self.fitted:
            string += "\n\nThis optimizer has been fitted."
        else:
            string += "\n\nThis optimizer has NOT been fitted."
        return string

    def _initialize(self):
        """
        Initializes the model by creating the various matrices and generating the list of available nodes
        先將該模型初始化
        """
        assert self.map.shape[0] == self.map.shape[1], "Map is not a distance matrix!"
        num_nodes = self.map.shape[0]
        self.pheromone_matrix = np.ones((num_nodes, num_nodes))
        # Remove the diagonal since there is no pheromone from node i to itself
        self.pheromone_matrix[np.eye(num_nodes) == 1] = 0
        self.heuristic_matrix = 1 / self.map
        self.probability_matrix = (self.pheromone_matrix ** self.heuristic_alpha) * (
                self.heuristic_matrix ** self.heuristic_beta)  # element by element multiplcation
        self.set_of_available_nodes = list(range(num_nodes))

    def _reinstate_nodes(self):
        """
        Resets available nodes to all nodes for the next iteration
        在新的迭代之前先重設所有可用節點
        """
        self.set_of_available_nodes = list(range(self.map.shape[0]))

    def _update_probabilities(self):
        """
        After evaporation and intensification, the probability matrix needs to be updated.
        再進行完費洛蒙的消散與加強之後，可能矩陣需要再進行更新
        """
        self.probability_matrix = (self.pheromone_matrix ** self.heuristic_alpha) * (
                self.heuristic_matrix ** self.heuristic_beta)

    def _choose_next_node(self, from_node):
        """
        透過可能矩陣尋找通往下一個節點的路徑 如果p < p_choose_best 則會選擇最佳路徑
        Chooses the next node based on probabilities.  If p < p_choose_best, then the best path is chosen, otherwise
        it is selected from a probability distribution weighted by the pheromone.
        from_node: the node the ant is coming from
        return: index of the node the ant is going to
        """
        numerator = self.probability_matrix[from_node, self.set_of_available_nodes]
        if np.random.random() < self.choose_best:
            next_node = np.argmax(numerator)
        else:
            denominator = np.sum(numerator)
            probabilities = numerator / denominator
            next_node = np.random.choice(range(len(probabilities)), p=probabilities)
        return next_node

    def _remove_node(self, node):
        self.set_of_available_nodes.remove(node)

    def _evaluate(self, paths, mode):
        """
        Evaluates the solutions of the ants by adding up the distances between nodes.
        paths: solutions from the ants
        mode: max or min
        return: x and y coordinates of the best path as a tuple, the best path, and the best score
        """
        scores = np.zeros(len(paths))
        coordinates_i = []
        coordinates_j = []
        for index, path in enumerate(paths):
            score = 0
            coords_i = []
            coords_j = []
            for i in range(len(path) - 1):
                coords_i.append(path[i])
                coords_j.append(path[i + 1])
                score += self.map[path[i], path[i + 1]]
            scores[index] = score
            coordinates_i.append(coords_i)
            coordinates_j.append(coords_j)
        if mode == 'min':
            best = np.argmin(scores)
        elif mode == 'max':
            best = np.argmax(scores)
        return (coordinates_i[best], coordinates_j[best]), paths[best], scores[best]

    def _evaporation(self):
        """
        Evaporate some pheromone as the inverse of the evaporation rate.  Also evaporates beta if desired.
        """
        self.pheromone_matrix *= (1 - self.evaporation_rate)
        self.heuristic_beta *= (1 - self.beta_evaporation_rate)

    def _intensify(self, best_coords):
        """
        Increases the pheromone by some scalar for the best route.
        best_coords: x and y (i and j) coordinates of the best route
        """
        i = best_coords[0]
        j = best_coords[1]
        self.pheromone_matrix[i, j] += self.pheromone_intensification

    def fit(self, map_matrix, iterations=100, mode='min', early_stopping_count=20, verbose=True):
        """
        Fits the ACO to a specific map.  This was designed with the Traveling Salesman problem in mind.
        map_matrix: Distance matrix or some other matrix with similar properties
        iterations: number of iterations
        mode: whether to get the minimum path or maximum path
        early_stopping_count: how many iterations of the same score to make the algorithm stop early
        return: the best score
        """
        #if verbose: print("Beginning ACO Optimization with {} iterations...".format(iterations))
        self.map = map_matrix
        start = time.time()
        self._initialize()
        num_equal = 0

        for i in range(iterations):
            start_iter = time.time()
            paths = []
            path = []

            for ant in range(self.ants):
                current_node = self.set_of_available_nodes[np.random.randint(0, len(self.set_of_available_nodes))]
                start_node = current_node
                while True:
                    path.append(current_node)
                    self._remove_node(current_node)
                    if len(self.set_of_available_nodes) != 0:
                        current_node_index = self._choose_next_node(current_node)
                        current_node = self.set_of_available_nodes[current_node_index]
                    else:
                        break

                path.append(start_node)  # go back to start
                self._reinstate_nodes()
                paths.append(path)
                path = []

            best_path_coords, best_path, best_score = self._evaluate(paths, mode)

            if i == 0:
                best_score_so_far = best_score
            else:
                if mode == 'min':
                    if best_score < best_score_so_far:
                        best_score_so_far = best_score
                        self.best_path = best_path
                elif mode == 'max':
                    if best_score > best_score_so_far:
                        best_score_so_far = best_score
                        self.best_path = best_path

            if best_score == best_score_so_far:
                num_equal += 1
            else:
                num_equal = 0

            self.best_series.append(best_score)
            self._evaporation()
            self._intensify(best_path_coords)
            self._update_probabilities()
            
            if best_score == best_score_so_far and num_equal == early_stopping_count:
                self.stopped_early = True
                print("Stopping early due to {} iterations of the same score.".format(early_stopping_count))
                break

        self.fit_time = round(time.time() - start)
        self.fitted = True

        if mode == 'min':
            self.best = self.best_series[np.argmin(self.best_series)]
            if verbose: print(
                "ACO fitted.   Best score: {}".format(self.best))
            return self.best
        elif mode == 'max':
            self.best = self.best_series[np.argmax(self.best_series)]
            if verbose: print(
                "ACO fitted.   Best score: {}".format(self.best))
            return self.best
        else:
            raise ValueError("Invalid mode!  Choose 'min' or 'max'.")

average_times_list = [] #平均次數
dp_time_list = [] #dp執行時間
ant_time_list = [] #ant執行時間


for i in range(4,21,1): #i represents number of point
    
    dp_average_time = 0
    ant_average_time = 0
    average_times = 0
    
    for j in range(5): # j is used to run the repetitive number of point
        print("                     頂點數{}                     ".format(i))
        print("---------------------round{}----------------------".format(j+1))
        
        dp_start_time = time.time() #find dp start time
        dp_TSP(i)                 #i represents number of point and this function takes advantage of dp
        dp_end_time = time.time() # find dp end time
        dp_average_time += dp_end_time - dp_start_time # calculate dp running time
        
        problem = np.array(matrix) #transform list into array for antOptimizer
        ant_start_time = time.time() #find ant start time
        optimizer = AntColonyOptimizer(ants=10, evaporation_rate=.1, intensification=2, alpha=1, beta=1,
                               beta_evaporation_rate=0, choose_best=.1)  #construct optimizer
        best = optimizer.fit(problem, 100) #fit the array into the optimizer
        ant_end_time = time.time() # find ant end time
        ant_average_time += ant_end_time - ant_start_time # calculate ant running time
        average_times += (optimizer.best - g[(1, subset_k)]) / (g[(1, subset_k)]) # calculate the error between dp and ant
        print()
        print()
        
    average_times_list.append(average_times/5) #store the average_error into this list 
    dp_time_list.append(dp_average_time/5) #store dp running time
    ant_time_list.append(ant_average_time/5) # store ant running time


number_of_point = [i for i in range(4,21,1)] #x-axis

fig, (ax1, ax2) = plt.subplots(1, 2, sharex = True, sharey = False, figsize = (12, 4.5)) #divide into two plots

ax1.plot(number_of_point,dp_time_list,'o-',color='g',label='dp')
ax1.plot(number_of_point,ant_time_list,'s-',color='r',label='ant')
ax1.set_xlabel("number_of_point",fontsize=15)
ax1.set_ylabel("running_time",fontsize=15)
ax1.legend(loc = "best", fontsize=20)

ax2.plot(number_of_point,average_times_list,'x-',color='y',label='average_times')
ax2.set_xlabel("number_of_point",fontsize=15)
ax2.set_ylabel("error",fontsize=15)
fig.show()


