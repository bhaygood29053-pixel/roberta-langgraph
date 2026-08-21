
Beyond immediate optimizations, this methodology addresses the inherent quadratic complexity of
traditional consensus models, where consensus complexity scales as O(n2) due to the need for all
validators to communicate across the network. Without intervention, as the validator set expands, the
sheer volume of communication required would exponentially increase, even if transaction throughput
remains constant. A widely adopted solution—seen in protocols such as HotStuff2 [4], Avalanche’s
“neighborhoods”[5], and Ethereum’s attestation committees—is to introduce subcommittees. This refinement
reduces consensus complexity from O(n2) to O(k2), where k represents the subcommittee size.

### 4.3 Optimizing Consensus for Scalability

By structuring consensus around dynamically formed, efficient voting groups, X1 Blockchain optimizes
scalability, minimizes latency, and significantly reduces the computational load on block leaders. This
subcommittee-based structure ensures that consensus remains both performant and decentralized, even as
network participation scales over time.

## 5. Dynamic Base Fee Mechanism

X1 Blockchain employs a dynamic base fee mechanism inspired by Ethereum’s EIP-1559 to optimize
transaction pricing and ensure network sustainability. Unlike other blockchains where base fees are set
too low, leading to unchecked spam transactions, X1 Blockchain enforces a base fee that dynamically
adjusts based on compute units (CU) and overall blockchain load. This ensures that transaction fees
accurately reflect network resource consumption, preventing congestion and enhancing economic
efficiency. By implementing an adaptive auction system, X1 Blockchain dynamically prices block space,
leveraging statistical analysis of compute units (CU) and real-time network activity. This dual-factor
pricing model ensures that fees are allocated efficiently and fairly, preventing manipulation and
enabling sustainable network usage. Additionally, a portion of the transaction fees is burned, reducing
native token net-inflation and promoting long-term economic stability.

> Figure 4: Comparison of how different blockchains scale based on Big O Notation. X1 Blockchain achieves O(1) complexity, indicating minimal scaling difficulty with increasing network size, while other chains such as Solana and Fantom face O(n2) complexity.

### 5.1 Key Benefits of this Approach

- Efficient Block Space Pricing: Implements a dual-factor pricing system that considers both computational demand and overall network load, preventing unnecessary congestion while maintaining fair fee dynamics.

- Spam Reduction: Enforces a dynamic base fee that discourages excessive low-value bids, preventing network spam while keeping transaction costs predictable and sustainable.

- MEV Mitigation: Introduces statistical fee adjustments that prevent artificial congestion and manipulative bidding, ensuring fairer transaction execution and reducing toxic MEV extraction.

By integrating these mechanisms, X1 Blockchain optimizes economic sustainability, enhances network
security, and ensures that transaction pricing remains both efficient and equitable across all network
participants.

> Figure 5: Visualization of X1 Blockchain’s dynamic base fee mechanism. The fee increases progressively as the block fills up, with block capacity measured in Compute Units (CU) across threads.

> Figure 6: Diagram illustrating how transaction fees are calculated on X1 Blockchain. The total transaction cost is determined by the base fee (txCU × M) and an optional priority fee set by the sender.

### 5.2 Staking Incentives and Fee Adjustments

X1 Blockchain introduces a strategic enhancement to its dynamic base fee mechanism by incorporating fee
adjustments that are influenced by participant staking. This innovative feature decreases base fees in
proportion to the amount of tokens staked and the duration for which they are locked. The primary goal
of this approach is to incentivize network participation through staking, thereby aligning participant
activities with the broader objectives of network health and security. The integration of staking
incentives into the fee structure not only encourages participants to stake their tokens but also
rewards them with reduced transaction costs. This reduction is scaled by both the volume of tokens
staked and the length of time they are committed to the network, promoting long-term participation and
investment in the stability of the blockchain. As participants are motivated to lock in their tokens for
extended periods, the network benefits from enhanced security and a more robust consensus mechanism.
Moreover, this fee adjustment mechanism serves to mitigate potential economic barriers for active
participants by lowering the cost of transactions for those who contribute significantly to the
network’s capital. This fosters a more inclusive economic environment and ensures that the blockchain
remains accessible and sustainable. By dynamically adjusting transaction fees based on staking
parameters, X1 Blockchain not only enhances its economic model but also fortifies network security and
encourages a deeper commitment from its participants, ensuring long-term growth and stability.

## 6. Decentralized MEV Handling and Fair Extraction

X1 blockchain integrates native MEV block engine within framework, reducing the proliferation of
third-party MEV block builders and ensuring a more decentralized and transparent approach to MEV
extraction.

### 6.1 Native MEV Block Engine and Validator Integration

Unlike traditional blockchains where MEV opportunities are dominated by private searchers and external
builders, X1 Blockchain fights MEV centralization by incorporating an MEV block engine directly into its
validator infrastructure. This integration enables validators to participate in MEV extraction
autonomously, eliminating dependence on third-party intermediaries and promoting a fairer, more
decentralized ecosystem.

### 6.2 Reducing MEV Centralization Through Fair Rewards Distribution
