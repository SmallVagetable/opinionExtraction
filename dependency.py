from pyhanlp import JClass
import operator

class DependencyExtraction(object):

    def __init__(self):
        self.hanlp = JClass('com.hankcs.hanlp.HanLP')
        self.jump_relation = set(['定中关系', '状中结构', '主谓关系'])
        self.reverse_relation = set(['动补结构', '动宾关系', '介宾关系'])
        self.main_relation = set(['核心关系'])
        self.remove_relate = set(['标点符号'])
        self.include = set()
        self.group = {}

    # 句子的观点提取，单root，从root出发，1.找前面最近的修饰词。2.找后面距离为1的reverse_relation
    def parseSentence(self, sentence):
        reverse_target = {}
        parse_result = str(self.hanlp.parseDependency(sentence)).strip().split('\n')
        for p in parse_result:
            print(p)
        for i in range(len(parse_result)):
            parse_result[i] = parse_result[i].split('\t')
            self_index = int(parse_result[i][0])
            target_index = int(parse_result[i][6])
            relation = parse_result[i][7]
            if relation in self.remove_relate:
                continue
            if target_index > self_index:
                reverse_target[target_index] = self_index
        result = {}
        checked = set()
        related_words = set()
        for item in parse_result:
            relation = item[7]
            target = int(item[6])
            index = int(item[0])
            if index in checked:
                continue
            while relation in self.jump_relation:
                checked.add(index)
                next_item = parse_result[target - 1]
                relation = next_item[7]
                target = int(next_item[6])
                index = int(next_item[0])

            if relation in self.reverse_relation and target in result and target not in related_words:
                result[index] = parse_result[index - 1][1]
                if index in reverse_target:
                    reverse_target_index = reverse_target[index]
                    if abs(index - reverse_target[index]) <= 1:
                        result[reverse_target_index] = parse_result[reverse_target_index - 1][1]
                        related_words.add(reverse_target_index)

            if relation in self.main_relation:
                result[index] = parse_result[index - 1][1]
                if index in reverse_target:
                    reverse_target_index = reverse_target[index]
                    if abs(index - reverse_target_index) <= 1:
                        result[reverse_target_index] = parse_result[reverse_target_index - 1][1]
                        related_words.add(reverse_target_index)
            checked.add(index)

        for item in parse_result:
            word = item[1]
            if word in self.include:
                result[int(item[0])] = word

        sorted_keys = sorted(result.items(), key=operator.itemgetter(0))
        selected_words = [w[1] for w in sorted_keys]
        return selected_words

    ''' 
    关键词观点提取，根据关键词key，找到关键处的rootpath，寻找这个root中的观点，观点提取方式和parseSentence的基本一样。
    支持提取多个root的观点。
    '''
    def parseSentWithKey(self, sentence, key=None):
        if key:
            keyIndex = 0
            if key not in sentence:
                return []
        rootList = []
        parse_result = str(self.hanlp.parseDependency(sentence)).strip().split('\n')
        # 索引-1，改正确
        for i in range(len(parse_result)):
            parse_result[i] = parse_result[i].split('\t')
            parse_result[i][0] = int(parse_result[i][0]) - 1
            parse_result[i][6] = int(parse_result[i][6]) - 1
            if key and parse_result[i][1] == key:
                keyIndex = i

        for i in range(len(parse_result)):
            self_index = int(parse_result[i][0])
            target_index = int(parse_result[i][6])
            relation = parse_result[i][7]
            if relation in self.main_relation:
                if self_index not in rootList:
                    rootList.append(self_index)
            elif relation == "并列关系" and target_index in rootList:
                if self_index not in rootList:
                    rootList.append(self_index)

            if len(parse_result[target_index]) == 10:
                parse_result[target_index].append([])

            if target_index != -1 and not (relation == "并列关系" and target_index in rootList):
                parse_result[target_index][10].append(self_index)

        if key:
            rootIndex = 0
            if len(rootList) > 1:
                target = keyIndex
                while True:
                    if target in rootList:
                        rootIndex = rootList.index(target)
                        break
                    next_item = parse_result[target]
                    target = int(next_item[6])
            loopRoot = [rootList[rootIndex]]
        else:
            loopRoot = rootList

        result = {}
        related_words = set()
        for root in loopRoot:
            if key:
                self.addToResult(parse_result, keyIndex, result, related_words)
            self.addToResult(parse_result, root, result, related_words)

        for item in parse_result:
            relation = item[7]
            target = int(item[6])
            index = int(item[0])
            if relation in self.reverse_relation and target in result and target not in related_words:
                self.addToResult(parse_result, index, result, related_words)

        for item in parse_result:
            word = item[1]
            if word == key:
                result[int(item[0])] = word

        sorted_keys = sorted(result.items(), key=operator.itemgetter(0))
        selected_words = [w[1] for w in sorted_keys]
        return selected_words


    def addToResult(self, parse_result, index, result, related_words):
        result[index] = parse_result[index][1]
        if len(parse_result[index]) == 10:
            return
        reverse_target_index = 0
        for i in parse_result[index][10]:
            if i < index and i > reverse_target_index:
                reverse_target_index = i
        if abs(index - reverse_target_index) <= 1:
            result[reverse_target_index] = parse_result[reverse_target_index][1]
            related_words.add(reverse_target_index)