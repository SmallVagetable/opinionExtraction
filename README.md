# opinionExtraction

## 使用到的技术
1. pyhanlp的依存关系。--dependency.py
2. 观点相似度计算。我这里为了快速，用了difflib的相似度计算的方式。 --similarity
3. 从多个观点中，提取总结性的观点。--getSummary

## 数据形式
输入：句子的列表[sent1, sent2,sent3,...,sentn]

输出：观点频次从高到低的dict结构，key是一类观点的总结，value是一类观点的list

## requirements.txt
pyhanlp==0.1.44

## 入口
main.py

## 改进

- 相似度的计算方式可以改进
- 总结观点的提取
- 观点聚类的算法O(n2)的效率的改进
- pyhanlp中加入自己的词表 https://zhuanlan.zhihu.com/p/35780877
- pyhanlp中依存关系的提取方式改进
