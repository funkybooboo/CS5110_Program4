# Author: Nate Stott
# Date: 2/26/2024
# For: CS5110 - Multi-Agent Systems - Program 4

from copy import deepcopy
from numpy import random


def main():
    Election.simulation(20, 5, 1052, True)
    # Election.simulation(100, 5, 1052)
    # Election.simulation(1_000, 5, 1052)
    # Election.simulation(10_000, 5, 1052)
    # Election.simulation(100_000, 5, 1052)
    # Election.simulation(1_000_000, 5, 1052)


class Election:
    class Voter:
        def __init__(self, name: str, pk: int, election):
            self.name = name
            self.pk = pk  # primary key
            self.election = election
            self.connections = [0 for _ in range(self.election.voter_count)]
            self.ranked_candidates = []
            self.__create_connections()
            self.__rank_candidates()
            self.original_ranked_candidates = deepcopy(self.ranked_candidates)

        def __rank_candidates(self):
            if len(self.ranked_candidates) == 0:
                candidates = self.__create_candidates()
            else:
                candidates = self.ranked_candidates
            self.ranked_candidates = sorted(candidates, key=lambda candidate: candidate["score"], reverse=True)
            self.__set_candidate_place()

        def __create_connections(self):
            connection_count = round(random.uniform(0, self.election.voter_count / 2))
            for _ in range(connection_count):
                connect_to = random.randint(0, self.election.voter_count)
                if connect_to != self.pk:
                    self.connections[connect_to] = 1

        def __set_candidate_place(self):
            for candidate in self.ranked_candidates:
                candidate["place"] = self.ranked_candidates.index(candidate)

        def __create_candidates(self):
            candidates = []
            for i in range(self.election.candidate_count):
                candidate = {
                    "name": f"Candidate{i}",
                    "pk": i,
                    "score": round(random.randint(0, 100) / 10),
                    "place": 0
                }
                candidates.append(candidate)
            return candidates

        def print_connections(self):
            print(f"{self.name}  {self.connections}")

        def print_rankings(self):
            print(f"First choice for {self.name} is {self.ranked_candidates[0]['name']}")
            for candidate in self.ranked_candidates:
                print(f"\t{candidate['name']}: Score {candidate['score']}, Place {candidate['place']}")
            print(f"\tORDER: {[candidate['name'] for candidate in self.ranked_candidates]}")

        def cardinal_utility(self, winner_pk: int):
            return abs(self.ranked_candidates[0]["score"] - self.ranked_candidates[winner_pk]["score"])

        def ordinal_utility(self, winner_pk: int):
            return abs(self.ranked_candidates[0]["place"] - self.ranked_candidates[winner_pk]["place"])

        def vote(self):
            return self.ranked_candidates[0]["pk"]

        def social_network_vote(self):
            connections_vote_information, connection_count = self.__get_connections_vote_information()
            if len(connections_vote_information) == 0:
                return self.vote()
            connections_candidates_information = self.__get_candidates_information(connections_vote_information)
            sorted_connections_candidates_information = {
                "vote_count": sorted(connections_candidates_information,
                                     key=lambda candidate: candidate["vote_count"],
                                     reverse=True),
                "average_score": sorted(connections_candidates_information,
                                        key=lambda candidate: candidate["average_score"],
                                        reverse=True),
                "average_place": sorted(connections_candidates_information,
                                        key=lambda candidate: candidate["average_place"])
            }
            return self.__get_social_vote(sorted_connections_candidates_information, connection_count)

        def __get_social_vote(self, sorted_connections_candidates_information, connection_count):
            # I want to vote for the candidate that has the highest average score and the lowest average place
            # I also want to vote for the candidate that has the most votes because that candidate is more likely to win
            # I also want to vote for someone that I am okay with winning
            vote_pk = self.vote()
            if sorted_connections_candidates_information["vote_count"][0]["pk"] == vote_pk:
                vote_pk = sorted_connections_candidates_information["their_vote_count"][0]["pk"]
            elif sorted_connections_candidates_information["average_score"][0]["pk"] == vote_pk:
                vote_pk = sorted_connections_candidates_information["average_place"][0]["pk"]
            elif sorted_connections_candidates_information["average_place"][0]["pk"] == vote_pk:
                vote_pk = sorted_connections_candidates_information["average_place"][0]["pk"]
            else:
                vote_pk = self.__get_candidate_im_ok_with(connection_count, sorted_connections_candidates_information, vote_pk)
            return vote_pk

        def __get_candidate_im_ok_with(self, connection_count, sorted_connections_candidates_information, vote_pk):
            my_average_score = self.__get_my_average_score()
            for candidate in sorted_connections_candidates_information["vote_count"]:
                my_score, my_place = self.__get_how_i_feel_about_candidate(candidate["pk"])
                if my_score is None or my_place is None:
                    # I don't know about this candidate
                    continue
                is_likely_to_win = candidate["vote_count"] >= connection_count / 2
                they_like_them_as_much_as_me = candidate["average_score"] >= my_average_score and candidate["average_place"] <= self.election.candidate_count / 2
                i_am_ok_with_them_winning = my_score >= my_average_score and my_place <= self.election.candidate_count / 2
                if is_likely_to_win and i_am_ok_with_them_winning and they_like_them_as_much_as_me:
                    vote_pk = candidate["pk"]
                    break
            return vote_pk

        def __get_my_average_score(self):
            my_average_score = 0
            for candidate in self.ranked_candidates:
                my_average_score += candidate["score"]
            return my_average_score / len(self.ranked_candidates)

        def __get_how_i_feel_about_candidate(self, candidate_pk):
            for candidate in self.ranked_candidates:
                if candidate["pk"] == candidate_pk:
                    return candidate["score"], candidate["place"]
            return None, None

        def __get_candidates_information(self, connections_vote_information):
            candidates_information = []
            for candidate in self.ranked_candidates:
                candidates_information.append({
                    "pk": candidate["pk"],
                    "name": candidate["name"],
                    "average_score": self.__get_average_score(candidate["pk"], connections_vote_information),
                    "average_place": self.__get_average_place(candidate["pk"], connections_vote_information),
                    "vote_count": self.__get_candidate_vote_count(candidate["pk"], connections_vote_information)
                })
            return candidates_information

        @staticmethod
        def __get_average_place(candidate_pk: int, connections_vote_information):
            place_sum = 0
            vote_count = 0
            for vote in connections_vote_information:
                if vote["vote_pk"] == candidate_pk:
                    place_sum += vote["vote_place"]
                    vote_count += 1
            if vote_count == 0:
                return 0
            return place_sum / vote_count

        @staticmethod
        def __get_average_score(candidate_pk: int, connections_vote_information):
            score_sum = 0
            vote_count = 0
            for vote in connections_vote_information:
                if vote["vote_pk"] == candidate_pk:
                    score_sum += vote["vote_score"]
                    vote_count += 1
            if vote_count == 0:
                return 0
            return score_sum / vote_count

        @staticmethod
        def __get_candidate_vote_count(candidate_pk: int, connections_vote_information):
            vote_count = 0
            for vote in connections_vote_information:
                if vote["vote_pk"] == candidate_pk:
                    vote_count += 1
            if vote_count == 0:
                return 0
            return vote_count

        def __get_connections_vote_information(self):
            connection_votes = []
            connection_count = 0
            for pk, connection in enumerate(self.connections):
                if connection == 1:
                    connection_count += 1
                    connection_votes.append({
                        "pk": pk,
                        "name": self.election.voters[pk].name,
                        "vote_name": self.election.voters[pk].ranked_candidates[0]["name"],
                        "vote_pk": self.election.voters[pk].ranked_candidates[0]["pk"],
                        "vote_score": self.election.voters[pk].ranked_candidates[0]["score"],
                        "vote_place": self.election.voters[pk].ranked_candidates[0]["place"]
                    })
            return connection_votes, connection_count

        def remove_candidate(self, candidate_pk: int):
            for candidate in self.ranked_candidates:
                if candidate["pk"] == candidate_pk:
                    self.ranked_candidates.remove(candidate)
                    break
            self.__rank_candidates()

        def rest_ranked_candidates(self):
            self.ranked_candidates = deepcopy(self.original_ranked_candidates)

    def __init__(self, voter_count: int, candidate_count: int, seed: int, verbose: bool = False):
        random.seed(seed)
        self.voter_count = voter_count
        self.candidate_count = candidate_count
        self.verbose = verbose
        self.voters = []
        for i in range(voter_count):
            self.voters.append(self.Voter(f"Voter{i}", i, self))

    def statistics(self):
        if self.verbose:
            self.__print_connections()
            self.__print_rankings()

    def __print_connections(self):
        print("CONNECTIONS")
        for voter in self.voters:
            voter.print_connections()

    def __print_rankings(self):
        print("RANKINGS")
        for voter in self.voters:
            voter.print_rankings()

    def __remove_candidate(self, candidate_pk: int):
        for voter in self.voters:
            voter.remove_candidate(candidate_pk)

    def __voter_welfare(self, winner_pk: int):
        for voter in self.voters:
            print(f"{voter.name}")
            print(f"\tCardinal Utility: {voter.cardinal_utility(winner_pk)}")
            print(f"\tOrdinal Utility: {voter.ordinal_utility(winner_pk)}")

    def __reset_candidates(self):
        for voter in self.voters:
            voter.rest_ranked_candidates()

    def first_past_the_post_voting(self, is_social_network: bool):
        print("FIRST PAST THE POST")
        self.__reset_candidates()
        if is_social_network:
            winner_pk, loser_pk = self.__social_network_vote()
        else:
            winner_pk, loser_pk = self.__vote()
        print("WINNER:", winner_pk)
        self.__voter_welfare(winner_pk)

    def ranked_choice_voting(self, is_social_network: bool):
        print("RANKED CHOICE")
        self.__reset_candidates()
        for _ in range(self.candidate_count - 1):
            if is_social_network:
                winner_pk, loser_pk = self.__social_network_vote()
            else:
                winner_pk, loser_pk = self.__vote()
            if self.verbose:
                print(f"ROUND WINNER: Candidate{winner_pk}")
                print(f"ROUND LOSER: Candidate{loser_pk}")
                self.__voter_welfare(winner_pk)
            self.__remove_candidate(loser_pk)
        if is_social_network:
            winner_pk, loser_pk = self.__social_network_vote()
        else:
            winner_pk, loser_pk = self.__vote()
        print(f"WINNER: Candidate{winner_pk}")
        self.__voter_welfare(winner_pk)

    def __vote(self):
        votes = [0 for _ in range(self.candidate_count)]
        for voter in self.voters:
            votes[voter.vote()] += 1
        winner_pk = votes.index(max(votes))
        loser_pk = votes.index(min(votes))
        return winner_pk, loser_pk

    def __social_network_vote(self):
        votes = [0 for _ in range(self.candidate_count)]
        for voter in self.voters:
            votes[voter.social_network_vote()] += 1
        winner_pk = votes.index(max(votes))
        loser_pk = votes.index(min(votes))
        return winner_pk, loser_pk

    @staticmethod
    def simulation(voter_count: int, candidate_count: int, seed: int, verbose: bool = False):
        print("*" * 50)
        print(f"VOTER COUNT: {voter_count}")
        print(f"CANDIDATE COUNT: {candidate_count}")
        print(f"SEED: {seed}")
        print(f"VERBOSE: {verbose}")
        print()
        election = Election(voter_count, candidate_count, seed, verbose)
        print()
        election.statistics()
        print()
        election.first_past_the_post_voting(False)
        print()
        election.ranked_choice_voting(False)
        print()
        election.first_past_the_post_voting(True)
        print()
        election.ranked_choice_voting(True)
        print()


if __name__ == '__main__':
    main()
