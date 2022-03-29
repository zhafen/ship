# ship
A deliverable impact estimator and project management tool.

## Buy-In
Central to ship is the concept of buy-in.
The more buy-in you have in a community, the more freedom to act in that community, and the more the community will back you up.
The goal therefore is to maximize buy-in, $B$.

$B = q( \mathbf{S} ) F( \mathbf{M}, \mathbf{S}) \sum_i n(\mathbf{m}_i, \mathbf{M}) b(\mathbf{m}_i) f(\mathbf{m}_i, \mathbf{S})$

$B_{\rm tot} = \sum_k q_k \sum_j F_{jk} \sum_i n_{ij} b_i f_{ik}$

### Derivation

At the smallest scale buy-in is how well a ship $\mathbf{S}$ is received by a market $\mathbf{M}$.

$B = B( \mathbf{M}, \mathbf{S})$

$B = F( \mathbf{M}, \mathbf{S}) \sum_i n(\mathbf{m}_i, \mathbf{M}) B(\mathbf{m}_i, \mathbf{S})$

Here $F( \mathbf{M}, \mathbf{S})$ is the overall fit between the ship and the market, $n(\mathbf{m}_i, \mathbf{M})$ is the number of members of the market segment $\mathbf{m}_i$ in the market, and $B(\mathbf{m}_i, \mathbf{S})$ is the buyin between the ship and a market segment.
This form is motivated by a simple idea:
how well a ship is received by the market is both the sum of the parts and the interaction as a whole.
Note that this equation is self-consistent with $\mathbf{M} = \mathbf{m}_i$ if $F( \mathbf{S}, \mathbf{m_j})=1$, as expected.

For individual market segments we parameterize $B(\mathbf{m}, \mathbf{S})$ as

$B(\mathbf{m}, \mathbf{S}) = q(\mathbf{S}) b(\mathbf{m}) f(\mathbf{m}, \mathbf{S})$,

where $q(\mathbf{S})$ is the quality of the ship, $b(\mathbf{m})$ is the value of the buy-in for a market segment, and $f(\mathbf{m}, \mathbf{S})$ is the fit of the ship to the market segment.
Substituting this back in, 

$B = q( \mathbf{S} ) F( \mathbf{M}, \mathbf{S}) \sum_i n(\mathbf{m}_i, \mathbf{M}) b(\mathbf{m}_i) f(\mathbf{m}_i, \mathbf{S})$

The net buy-in across all markets is...

$B_{\rm tot} = \sum_k q( \mathbf{S}_k ) \sum_j F( \mathbf{M}_j, \mathbf{S}_k) \sum_i n(\mathbf{m}_i, \mathbf{M}_j) b(\mathbf{m}_i) f(\mathbf{m}_i, \mathbf{S}_k)$

All the parenthesis make this appear messier than it is, so we'll use an equivalent notation:

$B_{\rm tot} = \sum_k q_k \sum_j F_{jk} \sum_i n_{ij} b_i f_{ik}$


### Maximizing $\Delta B$

As deliverable-creators, we have control over $\mathbf{S}_k$, i.e. the quality of the ship $q_k$, the fit of the ship with a given market $F_{jk}$, and the fit of the ship with a given market segment $f_{ik}$.
Taking the derivative of $B_{\rm tot}$ w.r.t to each, we get...

$\frac{ \partial B_{\rm tot}}{ \partial q_k} = \sum_{j} F_{jk} \sum_i n_{ij} b_i f_{ik}$

$\frac{ \partial B_{\rm tot}}{ \partial F_{jk}} = q_k \sum_i n_{ij} f_{ik}$

$\frac{ \partial B_{\rm tot}}{ \partial f_{ik}} = q_k b_i \sum_j n_{ij} F_{jk}$

Using these, change in $B$ can be placed in the context of $\frac{d B_{\rm tot} }{dt}$, $\frac{ \partial B_{\rm tot}}{ \partial X}$, or $\Delta B$.
