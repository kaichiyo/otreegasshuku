from otree.api import models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer, Page, WaitPage
import random # 確率計算のために random をインポート

doc = """
A repeated traveler's dilemma game.
Modification: The information about a partner's past consistency is incorrect with a 1/3 probability.
"""

class C(BaseConstants):
    NAME_IN_URL = 'travelers_dilemma_repeated'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 5
    MIN_CLAIM = 1
    MAX_CLAIM = 200
    REWARD = 20
    PENALTY = 20
    # /// 変更点1：誤報の確率を定数として設定 ///
    INCORRECT_INFO_PROB = 1/3


class Subsession(BaseSubsession):
    pass

def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        players = subsession.get_players()
        if len(players) % 2 != 0:
            raise Exception("参加者の合計人数は、ペアを作るために偶数である必要があります。")
        subsession.group_randomly()
    else:
        subsession.group_randomly(fixed_id_in_group=False)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    preliminary_claim = models.IntegerField(
        min=C.MIN_CLAIM,
        max=C.MAX_CLAIM,
        label=f"まず、{C.MIN_CLAIM}から{C.MAX_CLAIM}の間の整数を「事前申告」してください。"
    )
    final_claim = models.IntegerField(
        min=C.MIN_CLAIM,
        max=C.MAX_CLAIM,
        label=f"相手の事前申告を踏まえて、{C.MIN_CLAIM}から{C.MAX_CLAIM}の間の整数を「本申告」してください。"
    )
    is_consistent = models.BooleanField()
    # /// 変更点2：データ記録用のフィールドを追加 ///
    # プレイヤーに表示されたパートナー情報（真偽が逆の可能性あり）
    displayed_partner_consistency = models.BooleanField()
    # 表示された情報が正確だったかどうか
    signal_was_accurate = models.BooleanField()


# FUNCTIONS
def get_cumulative_payoff(player: Player):
    if player.round_number == 1:
        return 0
    return sum(p.payoff for p in player.in_rounds(1, player.round_number - 1))

def set_consistency(player: Player):
    player.is_consistent = (player.preliminary_claim == player.final_claim)

def set_payoffs(group: Group):
    for p in group.get_players():
        set_consistency(p)

    p1 = group.get_player_by_id(1)
    p2 = group.get_player_by_id(2)

    if p1.final_claim < p2.final_claim:
        p1.payoff = p1.final_claim + C.REWARD
        p2.payoff = p1.final_claim - C.PENALTY
    elif p2.final_claim < p1.final_claim:
        p2.payoff = p2.final_claim + C.REWARD
        p1.payoff = p2.final_claim - C.PENALTY
    else:
        p1.payoff = p1.final_claim
        p2.payoff = p2.final_claim


def get_partner(player: Player):
    return player.get_others_in_group()[0]


# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PreliminaryClaim(Page):
    form_model = 'player'
    form_fields = ['preliminary_claim']
    
    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        partner_history_displayed = None

        if player.round_number > 1:
            partner_prev_round = partner.in_round(player.round_number - 1)
            # パートナーの前回のラウンドでの実際の行動
            actual_consistency = partner_prev_round.is_consistent
            
            # /// 変更点3：確率で情報を反転させるロジック ///
            if random.random() < C.INCORRECT_INFO_PROB:
                # 確率1/3で、真偽が逆の情報が表示される
                displayed_consistency = not actual_consistency
                player.signal_was_accurate = False
            else:
                # 確率2/3で、正しい情報が表示される
                displayed_consistency = actual_consistency
                player.signal_was_accurate = True
            
            # 表示用の情報を辞書に格納
            partner_history_displayed = {'was_consistent': displayed_consistency}
            # 記録用の情報をモデルフィールドに保存
            player.displayed_partner_consistency = displayed_consistency

        return dict(
            partner=partner,
            partner_history=partner_history_displayed, # HTMLにはこの表示用の情報を渡す
            cumulative_payoff=get_cumulative_payoff(player)
        )

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number <= C.NUM_ROUNDS


class PreClaimWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number <= C.NUM_ROUNDS


class FinalClaim(Page):
    form_model = 'player'
    form_fields = ['final_claim']

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(
            partner=partner,
            preliminary_claim=partner.preliminary_claim,
            cumulative_payoff=get_cumulative_payoff(player)
        )
    
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number <= C.NUM_ROUNDS


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number <= C.NUM_ROUNDS


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(
            partner=partner,
            cumulative_payoff=get_cumulative_payoff(player)
        )
    
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number <= C.NUM_ROUNDS


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        total_payoff = sum(p.payoff for p in player.in_all_rounds())
        return {
            'total_payoff': total_payoff,
        }


page_sequence = [
    Introduction,
    Instructions,
    PreliminaryClaim,
    PreClaimWaitPage,
    FinalClaim,
    ResultsWaitPage,
    Results,
    FinalResults,
]