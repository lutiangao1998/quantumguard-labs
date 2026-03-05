from typing import Dict, List, Any

class QDAO:
    def __init__(self):
        self.proposals: Dict[str, Dict[str, Any]] = {}
        self.votes: Dict[str, Dict[str, bool]] = {}
        self.next_proposal_id = 1

    def create_proposal(self, proposer: str, title: str, description: str, snapshot_block: int) -> str:
        proposal_id = f"PROPOSAL-{self.next_proposal_id}"
        self.next_proposal_id += 1
        self.proposals[proposal_id] = {
            "proposer": proposer,
            "title": title,
            "description": description,
            "snapshot_block": snapshot_block,
            "status": "Pending", # Pending, Active, Succeeded, Defeated, Executed
            "for_votes": 0,
            "against_votes": 0,
            "voters": set() # Store unique voters
        }
        print(f"Proposal {proposal_id} created by {proposer}: {title}")
        return proposal_id

    def start_voting(self, proposal_id: str):
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        if self.proposals[proposal_id]["status"] != "Pending":
            raise ValueError("Voting can only start for pending proposals")
        self.proposals[proposal_id]["status"] = "Active"
        print(f"Voting started for proposal {proposal_id}")

    def vote(self, voter: str, proposal_id: str, support: bool, voting_power: int):
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        if self.proposals[proposal_id]["status"] != "Active":
            raise ValueError("Voting is not active for this proposal")
        if voter in self.proposals[proposal_id]["voters"]:
            raise ValueError("Voter already cast a vote for this proposal")

        if support:
            self.proposals[proposal_id]["for_votes"] += voting_power
        else:
            self.proposals[proposal_id]["against_votes"] += voting_power
        self.proposals[proposal_id]["voters"].add(voter)
        print(f"Voter {voter} cast {voting_power} votes {'for' if support else 'against'} proposal {proposal_id}")

    def end_voting(self, proposal_id: str, quorum_threshold: int, approval_threshold: float):
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        if self.proposals[proposal_id]["status"] != "Active":
            raise ValueError("Voting is not active for this proposal")

        total_votes = self.proposals[proposal_id]["for_votes"] + self.proposals[proposal_id]["against_votes"]
        if total_votes < quorum_threshold:
            self.proposals[proposal_id]["status"] = "Defeated"
            print(f"Proposal {proposal_id} defeated: Quorum not met")
            return

        if self.proposals[proposal_id]["for_votes"] / total_votes >= approval_threshold:
            self.proposals[proposal_id]["status"] = "Succeeded"
            print(f"Proposal {proposal_id} succeeded")
        else:
            self.proposals[proposal_id]["status"] = "Defeated"
            print(f"Proposal {proposal_id} defeated: Approval threshold not met")

    def execute_proposal(self, proposal_id: str):
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        if self.proposals[proposal_id]["status"] != "Succeeded":
            raise ValueError("Only succeeded proposals can be executed")
        
        # In a real system, this would trigger on-chain execution of the proposal's payload
        self.proposals[proposal_id]["status"] = "Executed"
        print(f"Proposal {proposal_id} executed")

    def get_proposal_state(self, proposal_id: str) -> Dict[str, Any]:
        if proposal_id not in self.proposals:
            raise ValueError("Proposal not found")
        return self.proposals[proposal_id]

