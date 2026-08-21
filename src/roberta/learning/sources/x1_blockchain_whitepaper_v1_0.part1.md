lower coefficients due to high financial barriers, such as stake concentration and high validator
operation costs. With a larger number of active validators distributed across a diverse network, X1
Blockchain is better equipped to resist censorship, attacks, and validator collusion, offering enhanced
security and reliability. Lower entry barriers also ensure that the network remains adaptable and
continuously scalable, as new participants can onboard without being hindered by prohibitive hardware or
financial constraints. As a result, X1 Blockchain creates a dynamic ecosystem where validator
participation remains balanced, supporting sustainable long-term growth and innovation. This approach
ensures:

- Lower operational costs for validators, improving profitability.

- A diverse validator set that resists censorship and collusion.

- A high Nakamoto Coefficient, reflecting better decentralization than many existing Layer-1 networks.

> Figure 1: The validator financial model on X1 Blockchain, illustrating how validators earn revenue and profit from network participation.

> Figure 2: Comparison of the decentralization and censorship resistance of blockchains, as measured by the Nakamoto Coefficient, alongside their parallel processing and smart contract capabilities.

## 3. Leader Selection Mechanism

X1 Blockchain leverages a monolithic architecture to maximize transaction throughput while maintaining
decentralization. Unlike modular blockchains that separate execution, consensus, and data availability
layers, X1 Blockchain retains all these functions within a single network, ensuring atomic composability
and reducing complexity.

### 3.1 VRF-Based Leader Selection, Anti-Collusion Measures, and Leader Schedule Optimization

X1 Blockchain employs a Proof-of-Stake (PoS) leader selection mechanism that leverages Verifiable Random
Functions (VRFs)—inspired by Cardano’s Ouroboros protocol [2]—to ensure fairness, unpredictability, and
decentralization in the block production process while maintaining efficiency and security. By
integrating the Anti-Collusion Protocol (ACP) into the leader selection mechanism, X1 prevents
validators from forming hidden alliances or manipulating stake distributions, reducing centralization
risks and promoting a more equitable block production process.

### 3.2 Key Features

- Enhanced Randomness and Verifiability: X1 Blockchain’s VRF-based leader selection enhances randomness and verifiability, ensuring that validators are selected pseudo-randomly based on their stake and performance. Each validator privately generates a random value that determines their eligibility for block production during a given epoch, reducing the risk of centralization and ensuring an unbiased leader selection process.

- Anti-Collusion Protection: The inclusion of the ACP mitigates scenarios where larger stakeholders would otherwise monopolize block production by disproportionately influencing consensus outcomes. Validators are continually monitored, and any signs of collusion or unfair influence trigger mechanisms to rebalance participation, ensuring no entity gains excessive control over the leader schedule.

- Balanced Stake Influence and Randomness: Validators with more stake have a higher probability of selection, but the pseudo-random nature of the VRF, combined with ACP protections, prevents any single validator or group from consistently dominating the network. The inclusion of the VRF proof in the block allows for public verification, ensuring that block producers are selected according to the protocol’s rules.

### 3.3 Performance-Based Leader Scheduling

Building upon this foundation, X1 Blockchain optimizes leader scheduling by dynamically preselecting
leaders, ensuring efficient block propagation and minimizing latency. The selection process incorporates
performance-based metrics, evaluating validators not only by stake but also by reliability and past
contributions. High-performing validators maintain consistent participation, while underperforming nodes
are deprioritized without exclusion, preserving network efficiency and resilience. This dynamic
scheduling mechanism adapts to network fluctuations, fostering a robust, decentralized system where
fairness and efficiency drive block production.

### 3.4 Minimizing Centralization Risks

Optimized performance-based leader selection and the fair distribution of block rewards through the
Anti-Collusion Protocol (ACP) and Verifiable Random Function (VRF) ensure that validators receive their
fair share of rewards while maintaining a decentralized block production process—minimizing the risk of
Proof-of-Stake (PoS) centralization over time.

> Figure 3: Factors determining block production eligibility on X1 Blockchain. These include stake weight, randomness (via VRF), and performance/reputation from recorded history.

## 4. Scalable Consensus Mechanism

### 4.1 Geographic Optimization and VRF-Based Consensus Participation

X1 Blockchain enhances consensus efficiency by implementing a subcommittee-based voting model within its
consensus protocol, together with a Verifiable Random Function (VRF)-based validator selection process
that considers validator geography. While validator votes do not directly influence transaction
execution—since they operate on separate threads from the four threads dedicated to transactions—a
tenfold increase in the validator set would significantly increase the leader’s workload, introducing
inefficiencies and degrading system performance. To mitigate this, X1 Blockchain leverages Solana’s
Proof of History (PoH) [3] as a cryptographic clock to structure voting more efficiently. PoH provides a
linear, verifiable sequence of events, allowing validators to incorporate a specific target PoH hash in
their block votes. This target hash is pseudo-random, universally fair, and resistant to manipulation,
ensuring vote integrity. As a result, the leader processes only a subset of votes based on the
designated target hash, significantly reducing computational overhead while preserving validator
participation. Importantly, all validators still receive rewards for their votes, maintaining incentives
and ensuring equitable participation without unnecessary resource strain.

### 4.2 Addressing Consensus Complexity
