from otree.api import models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer, Page, WaitPage
import random

doc = """
A repeated traveler's dilemma with fixed pairs.
A wait page is added after each round's results to sync players before the next round.
"""

class C(BaseConstants):
    NAME_IN_URL = 'travelers_dilemma_final'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 5
    MIN_CLAIM = 1
    MAX_CLAIM = 200
    AMOUNTS_LIST = [10, 20, 40, 80, 160]


class Subsession(BaseSubsession):
    bonus_penalty_amount = models.IntegerField()


def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        shuffled_amounts = random.sample(C.AMOUNTS_LIST, len(C.AMOUNTS_LIST))
        subsession.session.vars['round_amounts'] = shuffled_amounts
    current_round_amount = subsession.session.vars['round_amounts'][subsession.round_number - 1]
    subsession.bonus_penalty_amount = current_round_amount


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    participant_name = models.StringField(label="お名前（またはニックネーム）を入力してください。")
    preliminary_claim = models.IntegerField(
        min=C.MIN_CLAIM, max=C.MAX_CLAIM,
        label=f"まず、{C.MIN_CLAIM}から{C.MAX_CLAIM}の間の整数を「事前申告」してください。"
    )
    final_claim = models.IntegerField(
        min=C.MIN_CLAIM, max=C.MAX_CLAIM,
        label=f"相手の事前申告を踏まえて、{C.MIN_CLAIM}から{C.MAX_CLAIM}の間の整数を「本申告」してください。"
    )


# FUNCTIONS
def get_cumulative_payoff(player: Player):
    if player.round_number == 1: return 0
    return sum(p.payoff for p in player.in_rounds(1, player.round_number - 1))

def set_payoffs(group: Group):
    p1 = group.get_player_by_id(1)
    p2 = group.get_player_by_id(2)
    amount = group.subsession.bonus_penalty_amount
    if p1.final_claim < p2.final_claim:
        p1.payoff = p1.final_claim + amount
        p2.payoff = p1.final_claim - amount
    elif p2.final_claim < p1.final_claim:
        p2.payoff = p2.final_claim + amount
        p1.payoff = p2.final_claim - amount
    else:
        p1.payoff = p1.final_claim
        p2.payoff = p2.final_claim

def get_partner(player: Player):
    return player.get_others_in_group()[0]


# PAGES
class ParticipantName(Page):
    form_model = 'player'
    form_fields = ['participant_name']
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

class InstructionsWaitPage(WaitPage):
    body_text = "全員が説明を読み終えるまで、しばらくお待ちください。まもなくゲームが開始されます。"
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PreliminaryClaim(Page):
    form_model = 'player'
    form_fields = ['preliminary_claim']
    timeout_seconds = 120
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            if player.round_number == 1:
                player.preliminary_claim = C.MIN_CLAIM
            else:
                player.preliminary_claim = player.in_round(player.round_number - 1).preliminary_claim
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            cumulative_payoff=get_cumulative_payoff(player),
            bonus_penalty_amount=player.subsession.bonus_penalty_amount
        )

class PreClaimWaitPage(WaitPage):
    pass

class FinalClaim(Page):
    form_model = 'player'
    form_fields = ['final_claim']
    timeout_seconds = 120
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.final_claim = player.preliminary_claim
    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(
            preliminary_claim=partner.preliminary_claim,
            cumulative_payoff=get_cumulative_payoff(player),
            bonus_penalty_amount=player.subsession.bonus_penalty_amount
        )

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    timeout_seconds = 60
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            partner=get_partner(player),
            cumulative_payoff=get_cumulative_payoff(player)
        )

# /// 変更点：ここから ///
class RoundTransitionWaitPage(WaitPage):
    """次のラウンドに進む前に、全員の足並みをそろえるための待機ページ"""
    body_text = "パートナーが次のラウンドに進むのを待っています..."

    @staticmethod
    def is_displayed(player: Player):
        # 最終ラウンドの後 (FinalResultsの前) には表示しない
        return player.round_number < C.NUM_ROUNDS
# /// 変更点：ここまで ///


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS
    @staticmethod
    def vars_for_template(player: Player):
        total_payoff = sum(p.payoff for p in player.in_all_rounds())
        return {'total_payoff': total_payoff}


page_sequence = [
    ParticipantName,
    Introduction,
    Instructions,
    InstructionsWaitPage,
    PreliminaryClaim,
    PreClaimWaitPage,
    FinalClaim,
    ResultsWaitPage,
    Results,
    RoundTransitionWaitPage, # /// 変更点：ここに追加 ///
    FinalResults,
]