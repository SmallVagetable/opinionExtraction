
import difflib
import re
import json
import collections

from dependency import DependencyExtraction
from utils import readFile, findChineseWord


class Opinion(object):
    def __init__(self, sentence, opinion, keyword):
        self.opinion = opinion
        self.sentence = sentence
        self.keyword = keyword
        self.cluster = None

    def updateCluster(self, cluster):
        self.cluster = cluster


class OpinionCluster(object):

    def __init__(self):
        self._opinions = []

    def addOpinion(self, opinion):
        self._opinions.append(opinion)
        opinion.updateCluster(self)

    def getOpinions(self):
        return self._opinions

    def getSummary(self):
        # 对一个self._opinions生成一个标签，最长的句子，我们认为句子最长的，意思最完整
        maxLenStr = ""
        opinionStrs = []
        for op in self._opinions:
            opinion = op.opinion
            opinionStrs.append(opinion)
            if len(opinion) > len(maxLenStr):
                maxLenStr = opinion

        return maxLenStr
        # 统计字频率，减去边缘化的字
        # word_counter = collections.Counter(list("".join(opinionStrs))).most_common()
        #
        # newStr = []
        # maxNum = word_counter[0][1]
        # charList = list(maxLenStr)
        # for i, s in enumerate(charList):
        #     if not findChineseWord(s):
        #         newStr.append(s)
        #     # 不处理“能不能”，“是不是”，“有没有”
        #     elif i > 0 and s in ["不", "没"] and charList[i - 1] in ["能", "是", "有"]:
        #         newStr.append(s)
        #     else:
        #         # 过滤边缘化的字
        #         for word in word_counter:
        #             if word[0] == s and word[1] > maxNum / 3:
        #                 newStr.append(s)
        # return "".join(newStr)


class OpinionExtraction(object):

    def __init__(self, sentences = [], sentenceFile = "", keywordFile = ""):
        self.json_config = self.loadConfig()

        if sentenceFile:
            self.sentences = self.filterSentence(readFile(sentenceFile)[:self.json_config["dataLen"]])
        else:
            self.sentences = self.filterSentence(sentences[:self.json_config["dataLen"]])

        self.keyword = readFile(keywordFile)


    def loadConfig(self):
        f = open("./config.json", "r", encoding='utf-8')
        config = json.load(f)
        return config


    def filterSentence(self, sentences):
        # 正则匹配字母数字连续出现超过7个，包括账号，电话，邮箱，银行卡号
        newSentences = []
        email_phone_re = re.compile('[A-Za-z0-9\d]{7}')
        for sent in sentences:
            # 长度太短
            if len(sent) < 4:
                continue

            addFlag = True
            sentLower = sent.lower()

            # 关键字过滤
            for exceptWord in self.json_config["exceptWordList"]:
                if exceptWord in sentLower:
                    addFlag = False
                    break
            if not addFlag:
                continue

            # 不过滤的关键字
            for includeWord in self.json_config["includeWordList"]:
                if includeWord in sentLower:
                    newSentences.append(sent)
                    addFlag = False
                    break
            if not addFlag:
                continue

            # 重复过滤
            if sent in newSentences:
                continue

            # 过滤正则
            match = email_phone_re.findall(sentLower)
            if match:
                continue

            if addFlag:
                newSentences.append(sent)

        return newSentences


    def extractor(self):
        de = DependencyExtraction()
        opinionList = OpinionCluster()
        for sent in self.sentences:
            keyword = ""
            if not self.keyword:
                keyword = ""
            else:
                checkSent = []
                for word in self.keyword:
                    if sent not in checkSent and word in sent:
                        keyword = word
                        checkSent.append(sent)
                        break

            opinion = "".join(de.parseSentWithKey(sent, keyword))
            if self.filterOpinion(opinion):
                opinionList.addOpinion(Opinion(sent, opinion, keyword))

        #这步跳过前面的依存分析，加快调试
        # opinionList = self.getFirstCluster()

        '''
            这里设置两个阈值，先用小阈值把一个大数据切成小块，由于是小阈值，所以本身是一类的基本也能分到一类里面。
            由于分成了许多小块，再对每个小块做聚类，聚类速度大大提升，[0.2, 0.6]比[0.6]速度高30倍左右。
            但是[0.2, 0.6]和[0.6]最后的结果不是一样的，会把一些相同的观点拆开。
        '''
        thresholds = [0.2, 0.6]
        clusters = [opinionList]
        for threshold in thresholds:
            newClusters = []
            for cluster in clusters:
                newClusters += self.clusterOpinion(cluster, threshold)
            clusters = newClusters

        resMaxLen = {}
        for oc in clusters:
            if len(oc.getOpinions()) > self.json_config["minClusterLen"]:
                summaryStr = oc.getSummary()
                resMaxLen[summaryStr] = oc.getOpinions()

        return self.sortRes(resMaxLen)


    def sortRes(self, res):
        return sorted(res.items(), key=lambda item:len(item[1]), reverse=True)


    def getFirstCluster(self):
        opinions = []
        with open("./data/opinion.txt", "r", encoding="utf-8") as f:
            for line in f:
                lineSplit = line.strip().split(",")
                opinions.append(lineSplit)


        opinions = opinions[:self.json_config["dataLen"]]

        firstCluster = OpinionCluster()
        for op in opinions:
            firstCluster.addOpinion(Opinion(*op))
        return firstCluster


    def filterOpinion(self, opinion):
        check = True
        if len(opinion) <= self.json_config["minOpinionLen"]:
            check = False
        elif opinion.isdigit():
            check = False
        return check

    # 复杂度是O(n2)，速度比较慢。
    def clusterOpinion(self, cluster, threshold):
        opinions = cluster.getOpinions()
        num = len(opinions)
        clusters = []
        checked1 = []
        for i in range(num):
            oc = OpinionCluster()
            opinion1 = opinions[i]
            if opinion1 in checked1:
                continue
            if opinion1 not in oc.getOpinions():
                oc.addOpinion(opinion1)
            checked1.append(opinion1)
            for j in range(i + 1, num):
                opinion2 = opinions[j]
                if opinion2 in checked1:
                    continue
                sim = self.similarity(opinion1, opinion2)
                if sim > threshold:
                    if opinion2 not in oc.getOpinions():
                        oc.addOpinion(opinion2)
                    checked1.append(opinion2)
            clusters.append(oc)
        return clusters


    def similarity(self, o1, o2):
        return difflib.SequenceMatcher(a = o1.opinion, b = o2.opinion).quick_ratio()


