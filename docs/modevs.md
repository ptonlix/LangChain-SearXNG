## 🆚 AI 搜索模式对比测试

我筛选了 5 个有代表性的问题，分别对`AI+SearXNG` 、`智谱WebSearch`和`360AI搜索`
进行对比测试，初步分析一下各自特点。  
`AI+SearXNG` `智谱WebSearch` 大模型采用 智谱的`glm-3-turbo`

响应速度： `智谱WebSearch` > `360AI搜索` > `AI+SearXNG`  
内容质量： `360AI搜索` > `AI+SearXNG` ≈ `智谱WebSearch`

- 通过对比以下详细数据分析：

1. `360AI搜索`是我选择用来比较的标杆，毕竟 360AI 搜索本事数据和算力杠杠的。从生成的内容来看从响应时间和内容质量和逻辑性都不错，内容输出很全面，不愧是大厂产品。
2. `智谱WebSearch`响应速度是最快的，我猜测部分数据应该已经向量化到数据库了，而不是再去网上搜索，毕竟智谱的模型训练本身也需要大量的基础数据。从召回内容时间性上看，还做不到真正实时性，搜索引擎能力还需要进一步提升，部分提问可能不会去搜索而是直接回答，内容质量总体上一般。（可能和输入的 Prompt 有关系）  
   3.`AI+SearXNG`是通过 SearXNG 召回网页数据，再向量化过滤相似性文段后作为上下文再发给大模型，整体耗时最长在于向量化过滤相似性文段（可以进一步优化）。内容质量近似于`智谱WebSearch`,主要取决于 SearXNG 搜索的准确性和实时性，需要想办法提升搜索能力 SearXNG 搜索。（整体还有较大提升空间 🚀）

### 详细数据：

|                  搜索问题                   |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                AI+Searxng                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      智谱 WebSearch                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            360AI 搜索                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :-----------------------------------------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| 请问今天 NBA 掘金和森林狼的比赛结果怎么样？ |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     响应时间：12 秒<br>引用: 3 篇在线文章 <br>很抱歉，根据我现有的知识库，无法提供 2024 年 5 月 11 日之后的具体赛事结果，包括 NBA 掘金和森林狼的比赛。若您需要了解这场比赛的最终结果，建议查询最新的体育新闻报道或官方 NBA 赛事更新。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            响应时间：6 秒<br>引用：9 篇在线文章 <br>根据您提供的参考信息，2024 年 5 月 5 日 NBA 季后赛掘金队主场对阵森林狼队的比赛，最终以森林狼队获胜告终。森林狼队以 106-99 的比分击败了掘金队，爱德华兹在这场比赛中表现出色，全场轰下了 43 分、7 篮板和 3 助攻的数据，成为了全场的最佳球员。掘金队的核心球员约基奇虽然全场得到了 32 分、8 篮板和 9 助攻，但仍然无法带领球队取得胜利。此场比赛之后，森林狼队在双方的季后赛对决中占据了优势。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          响应时间：16 秒<br>引用: 30 篇在线文章 <br>2024 年 05 月 11 日 NBA 掘金和森林狼的比赛结果<br>根据给定的搜索结果，2024 年 05 月 11 日 NBA 季后赛西部半决赛第三回合的比赛是在掘金客场挑战森林狼。掘金队以 117:90 的比分击败了森林狼队，这场胜利使得掘金队将总比分扳成了 1:21。这场比赛也是森林狼本赛季季后赛的首次失利，此前他们以 2:0 领先掘金                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|      请介绍一下今年以来巴以冲突的情况       | 响应时间：177 秒<br>引用: 3 篇在线文章<br>今年以来，巴以冲突持续升温，具体情况如下：\n\n- 截至 2024 年 5 月 1 日，加沙地带卫生部门表示，在过去 24 小时内，以色列军队在加沙地带进行了 4 次军事行动，导致 33 人死亡、57 人受伤。自 2023 年 10 月 7 日新一轮巴以冲突爆发以来，以色列军队在加沙地带的军事行动已造成 34568 名巴勒斯坦人死亡、77765 人受伤[1]。\n\n- 2024 年 4 月 27 日，以色列军方表示，在巴勒斯坦加沙地带空袭了约 25 个目标。分析认为，以色列的长期军事行动使得巴以冲突有蔓延至中东其他地区的风险，甚至可能引发美国和伊朗等国家的直接冲突[2]。\n\n- 美国和越来越多的国家暂停向联合国在加沙的主要机构提供资金，原因是该机构的工作人员被指控参与了 2023 年 10 月 7 日哈马斯对以色列的袭击。联合国近东救济工程处已经解雇了数名员工[3]。\n\n- 2024 年 1 月 28 日，美国有线电视新闻网(CNN)的一名工作人员看到，被以色列军队在加沙拘留并被带到以色列边境的巴勒斯坦男子被蒙上眼睛，光着脚，双手被绑在背后。以色列军方称这些人涉嫌从事恐怖活动[3]。\n\n- 2023 年 12 月 7 日，以色列电视台播放的视频显示，在加沙，几十个男子一字排开，跪坐在地上，低着头，穿着内衣、蒙着眼睛，被以色列士兵看守着，这在社交网络上引发了激烈争论[4]。\n\n 以上信息显示，巴以冲突仍在持续，并造成了严重的人员伤亡。国际社会被呼吁向以色列施加更多压力，以避免冲突升级。否则，中东地区可能爆发一场波及整个地区的战争，对全球经济和安全形势产生严重影响[2]。 | 响应时间：12 秒<br>引用: 4 篇在线文章<br>今年以来，巴以冲突依然持续发酵，局势动荡不安。根据现有报道，自 2023 年 10 月 7 日新一轮巴以冲突爆发以来，截至 2024 年 5 月 1 日，加沙地带卫生部门表示，在过去 24 小时内，以色列军队在加沙地带进行了 4 次军事行动，导致 33 人死亡、57 人受伤。自冲突爆发以来，以色列军队在加沙地带的军事行动已造成 34568 名巴勒斯坦人死亡、77765 人受伤。\n\n2024 年 4 月 27 日，以色列军方表示，在过去的 24 小时内对加沙地带进行了约 25 个目标的空袭。同时，以色列国防军表示，预计将进行长期的作战，正在调整在加沙的部署。以色列同哈马斯的战争可能在 2024 年持续一整年，以色列军队已经做好长期作战的准备。\n\n 另一方面，美国与胡塞武装之间的冲突也日益加剧。美国军队击沉了三艘胡塞武装的船只，导致十名胡塞武装人员死亡。胡塞武装表示，美国应承担这一罪行的后果，并表示不会阻止其履行支持巴勒斯坦和加沙地带人道主义的义务。美国和英国已向胡塞武装发出最后通牒，警告其停止袭击红海商船，否则将采取军事行动。\n\n 此外，巴以冲突还引发了国际社会对人道主义状况的关注。美国和越来越多的国家暂停向联合国在加沙的主要机构提供资金，原因是该机构的工作人员被指控参与了 10 月 7 日哈马斯对以色列的袭击。联合国近东救济工程处已经解雇了数名员工。同时，飞地南部医院的情况正在恶化，物资供应减少，一个援助组织声称那里被以色列军队包围。\n\n 总的来说，今年以来巴以冲突依然激烈，局势动荡不安，造成了严重的人员伤亡和人道主义危机。国际社会呼吁各方保持克制，通过和平谈判解决争端，以避免冲突进一步升级。 | 响应时间：16 秒<br>引用: 30 篇在线文章<br>2024 年以来巴以冲突的情况<br>冲突概述<br>自 2024 年以来，巴以冲突（巴勒斯坦和以色列之间的冲突）仍然持续，并且造成了大量的人员伤亡和人道主义危机。这场冲突是中东地区历史上最为悠久和复杂的冲突之一 5。<br>冲突升级<br>2024 年 5 月 5 日晚，以色列军机对加沙南部城市拉法萨拉姆社区的一座房屋进行轰炸，导致多人伤亡 2。此后，以军在加沙地带的军事行动连续造成巴勒斯坦人的死亡和受伤 36。<br>国际反应<br>冲突引起了国际社会的广泛关注。哥伦比亚总统佩特罗在社交媒体上表示，由于以色列进攻拉法，国际刑事法院应该向以色列总理内塔尼亚胡发出国际逮捕令 6。此外，中国政府也对以色列的军事行动表示了严重关切，并强烈呼吁以色列停止进攻拉法 13。<br>停火谈判<br>尽管冲突激烈，但国际社会并未放弃和平努力。美国官员曾表示，美国预计以色列不会立即进攻拉法，并且美国正在与以色列官员讨论替代方案，以防止对拉法进行地面军事进攻 7。然而，这些努力并没有取得显著的效果，以军继续加强在拉法的军事行动 6。<br>人道主义危机<br>冲突导致了严重的人道主义危机。据报道，加沙地带已有 34943 名巴勒斯坦人死亡，78572 人受伤 63。联合国世界粮食计划署负责人警告说，如果对加沙北部飞地的援助不迅速增加，饥荒将迫在眉睫 11。<br>结论<br>2024 年以来的巴以冲突持续加剧，尽管有国际社会的调停努力，但双方的对立情绪似乎并未减弱。冲突已经造成了大量的人员伤亡和人道主义危机，使得该地区的和平前景变得越来越黯淡。 |
|           庆余年 2 什么时候上映？           |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   响应时间：28 秒<br>引用: 3 篇在线文章<br>《庆余年 2》已经定档，并将在 CCTV8 和腾讯同时播出。具体的播出日期在提供的参考信息中并未明确指出，只提到了该剧的制作班底在经过半年的杀青和审查后，终于迎来了播出。对于具体的播出时间，建议查阅最新的电视节目表或相关娱乐资讯                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          响应时间：12 秒<br>引用: 3 篇在线文章<br>《庆余年 2》已经定档，并将在 CCTV8 和腾讯同时播出。具体的播出日期在提供的参考信息中并未明确指出，只提到了该剧的制作班底在经过半年的杀青和审查后，终于迎来了播出。对于具体的播出时间，建议查阅最新的电视节目表或相关娱乐资讯。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              响应时间：17 秒<br>引用: 30 篇在线文章<br>《庆余年 2》的上映时间是 2024 年 5 月 16 日。这一天，该剧将在 CCTV-8 黄金强档 每日晚上 19:30 播出，并且会在 腾讯视频 全网独播。会员用户可以在每周一到周五晚上 19:30 更新 2 集，每周六、日更新 1 集，首更 4 集，SVIP 用户还可以享受提前看 1 集的特权 137915]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|     目前中国新能源汽车厂商排行榜是什么?     |                                                                                                                                                                                                                     响应时间：26 秒<br>引用: 3 篇在线文章<br>根据中商产业研究院发布的数据，中国新能源汽车厂商的销量排行榜显示，比亚迪汽车销量最高，达到 50.87 万辆，市场份额为 38.8%。特斯拉中国和广汽埃安分别排在第二和第三位，销量分别为 13.74 万辆和 8.03 万辆，市场份额分别为 10.5%和 6.1%。此外，上汽通用五菱、长安汽车、吉利汽车、理想汽车、蔚来汽车、哪吒汽车和华晨宝马也进入了前十名【1†来源】。在 2023 年 1-2 月期间，比亚迪新能源汽车的销量最高，达到 31.64 万辆，市场份额为 40.8%。特斯拉中国和上汽通用五菱分别排在第二和第三位，销量分别为 6.08 万辆和 5.04 万辆，市场份额分别为 7.8%和 6.5%。广汽埃安、长安汽车、吉利汽车、理想汽车、蔚来汽车、哪吒汽车和华晨宝马也位列前十名【2†来源】。而在 2023 年 10 月，埃安销量最高，达到 4.15 万辆，理想汽车紧随其后，销量突破 4 万辆。五菱缤果、小鹏汽车销量超 2 万辆，分别为 2.60 万辆和 2.00 万辆。零跑、赛力斯、蔚来、深蓝、极氪、问界进入前十名【3†来源】。                                                                                                                                                                                                                      |                                                                                                                                                                                                                                                                                                       响应时间：6 秒<br>引用: 0 篇在线文章<br>截至 2024 年 5 月 11 日，中国的新能源汽车市场持续快速发展，多家企业竞争激烈。根据市场份额、销量、技术创新等多方面因素，一些知名的中国新能源汽车厂商登上排行榜。\n\n 首先，比亚迪（BYD）长期以来一直是新能源汽车行业的领头羊，以其电池技术和电动车技术著称。其次，特斯拉（Tesla）虽然是一家外国公司，但在中国设有工厂，并且在中国市场有着显著的表现。此外，蔚来（NIO）、小鹏汽车（Xpeng）和理想汽车（Li Auto）等新势力汽车制造商，凭借其智能电动汽车也获得了广泛的关注和市场份额。\n\n 传统汽车制造商如吉利汽车（Geely）、长城汽车（Great Wall Motors）和广汽集团（GAC Group）等也纷纷推出了自己的新能源汽车品牌，积极转型以适应市场变化。\n\n 请注意，具体排名可能会随着时间和市场情况的变化而有所不同，因此查阅最新的行业报告和市场分析数据将获得最准确的排名信息。                                                                                                                                                                                                                                                                                                        |                                                                                                                                                                                                                        响应时间: 18 秒<br>引用: 30 篇在线文章<br>2024 年中国新能源汽车厂商排行榜<br>据最新的数据，我们可以看到中国新能源汽车市场的竞争日益激烈，各大厂商的销量和市场份额都在不断变化。以下是根据 2024 年 4 月和 1-3 月的销量数据整理出的部分中国新能源汽车厂商的排行榜：<br>1. 比亚迪<br>比亚迪作为中国新能源汽车的领导者，在 2024 年 4 月的销量排行榜中排名第一，其新能源汽车销量达到了很高的水平。比亚迪不仅在国内市场表现出色，在全球范围内也是重要的新能源汽车供应商之一 2。此外，比亚迪还在电池技术方面有着显著的优势 1。<br>2. 理想汽车<br>理想汽车在 2024 年 4 月的销量排行榜中位列第二，其理想 L9 等车型在各自细分市场都有不错的表现。理想汽车专注于用科技改变出行，是一家在美国纳斯达克和香港联交所上市的公司 1。<br>3. 问界<br>问界是赛力斯集团旗下的高端新能源汽车品牌，其问界 M5、问界 M7 等车型在市场上受到了消费者的欢迎，因此在 2024 年 4 月的销量排行榜中位列第三 1。...                                                                                                                                                                                                                         |
|      抖音目前最火的几个博主分别是谁？       |                                                                                                                                                                                                                                                                                           响应时间: 28 秒<br>引用: 3 篇在线文章<br>根据搜索结果，抖音目前最火的博主包括：\n\n1. 雷军：小米科技的创始人和 CEO，他的抖音个人账号拥有约 1858.7 万粉丝，发布的视频获得了约 5392.7 万的赞。[2][3]\n\n2. 兔头呀金融：分享理财、股票、基金等方面的知识，粉丝数量超过 1500 万。[5]\n\n3. 高火火：颜值高且唱歌好，抖音粉丝 4379.4 万，获赞 3.9 亿。[6]\n\n4. 郭聪明：唱歌好听的网红之一，抖音粉丝 4228.9 万，获赞 5.0 亿。[6]\n\n5. 大狼狗郑建鹏&言真夫妇：来自广东的夫妻博主，抖音粉丝已达 4133W。[6]\n\n6. 祝晓晗：抖音上火了很长时间的网红，粉丝 4073.2 万，获赞达到了 7 亿。[6]\n\n7. 李子柒：全网的网红，抖音粉丝有 4037 万，获赞 1.6 亿。[6]\n\n 以上是抖音目前几个粉丝数量非常庞大的博主，他们在各自的领域都有很高的影响力和知名度。[2][3][5][6]                                                                                                                                                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                                                                       响应时间: 9 秒<br>引用: 8 篇在线文章<br>关于抖音目前最火的博主，具体信息没有在提供的参考资料中明确指出。不过，从提供的资料[5]和[8]中我们可以了解到，抖音上有不同类型的博主受到关注，例如男扮女装一人分饰多角的博主、一人分饰多角的配音秀博主、探店博主、财经博主以及分享拍照技巧和国粹京剧的博主等。这些资料表明，抖音上的博主多样化和专业化，各自在不同的领域内拥有广泛的粉丝基础。\n\n 具体到最火的几个博主，由于参考资料未提供相关信息，我无法给出答案。通常这类信息需要根据最新的数据和流行趋势来确定，而这些信息可能会随时间和流行趋势的变化而变化。为了获得最准确的信息，建议直接访问抖音平台，查看当前的热门博主榜单或者使用抖音的搜索和推荐功能来了解最新的热门博主。                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                响应时间: 9 秒<br>引用: 8 篇在线文章<br>抖音最火的博主概览<br>根据最新的搜索结果，以下是抖音上几位非常火的博主：<br>1. 高火火<br>简介：高火火原名高宏鹏，是一位来自吉林延边的抖音博主，他的直播主要以唱歌娱乐为主，发布的短视频也广受粉丝的喜爱。<br>影响力：他在抖音上的知名度非常高，每一次更新都会引起热议。<br>2. 一禅小和尚<br>简介：一禅小和尚是一个视频创作团队的视频，视频内容像动画一样，虽然每个短视频的时长都很短，但里面的视频总能以特殊的哲理戳中许多网友的心巴。<br>影响力：他的视频在网络上非常受欢迎，能够以独特的视角看待生活中的问题。<br>3. 大狼狗郑建鹏<br>简介：大狼狗郑建鹏是一位舞蹈演员，同时也是一位货真价实的富二代，近几年在抖音平台也迅速的火了起来，借自己和家人的搞笑幽默的视频，深深赢得了许多观众的喜爱。<br>影响力：他的视频以其幽默搞笑的内容吸引了大量的粉丝。                                                                                                                                                                                                                                                                 |