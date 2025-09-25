from otree.api import models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer, Page, WaitPage
import random

doc = """
A repeated traveler's dilemma game.
Modifications:
- Participants enter their name at the beginning.
- Timeouts are set for claim and results pages with automatic submissions.
"""

class C(BaseConstants):
    NAME_IN_URL = 'travelers_dilemma_repeated'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 5
    MIN_CLAIM = 1
    MAX_CLAIM = 200
    REWARD = 20
    PENALTY = 20
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
    # /// 変更点1：名前を入力するフィールドを追加 ///
    participant_name = models.StringField(label="お名前（またはニックネーム）を入力してください。")

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
    displayed_partner_consistency = models.BooleanField()
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
# /// 変更点1：名前を入力するページを新しく追加 ///
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


class PreliminaryClaim(Page):
    form_model = 'player'
    form_fields = ['preliminary_claim']
    # /// 変更点2：タイムアウトを2分に設定 ///
    timeout_seconds = 120

    # /// 変更点3：タイムアウト時の処理を追加 ///
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            if player.round_number == 1:
                player.preliminary_claim = C.MIN_CLAIM
            else:
                player.preliminary_claim = player.in_round(player.round_number - 1).preliminary_claim
    
    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        partner_history_displayed = None
        if player.round_number > 1:
            partner_prev_round = partner.in_round(player.round_number - 1)
            actual_consistency = partner_prev_round.is_consistent
            if random.random() < C.INCORRECT_INFO_PROB:
                displayed_consistency = not actual_consistency
                player.signal_was_accurate = False
            else:
                displayed_consistency = actual_consistency
                player.signal_was_accurate = True
            partner_history_displayed = {'was_consistent': displayed_consistency}
            player.displayed_partner_consistency = displayed_consistency
        return dict(
            partner=partner,
            partner_history=partner_history_displayed,
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
    # /// 変更点2：タイムアウトを2分に設定 ///
    timeout_seconds = 120

    # /// 変更点3：タイムアウト時の処理を追加 ///
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.final_claim = player.preliminary_claim

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
    # /// 変更点2：タイムアウトを1分に設定 ///
    timeout_seconds = 60
    
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


# /// 変更点1：ページシーケンスの先頭に ParticipantName を追加 ///
page_sequence = [
    ParticipantName,
    Introduction,
    Instructions,
    PreliminaryClaim,
    PreClaimWaitPage,
    FinalClaim,
    ResultsWaitPage,
    Results,
    FinalResults,
]