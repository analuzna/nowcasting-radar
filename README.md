# Modelo de Nowcasting para datos de RMA1 con redes CNN-LSTM


La idea es que tenemos datos de **COLMAX** (después queremos que sea extensible al resto de variables pol) más alguna otra variable que definimos como **TOPE DE NUBE** y **rho_hv**. 

Los datos se van a regrillar y procesar en una etapa del proyecto (procesamiento datasets), se dividirán en secuencias de 6hs para de las cuales 3 serán de input y 3 de output. Se pueden secuenciar también 2hs 1hs de input y 1h de forecast. 

El modelo se define como una conv-lstm basado en el paper de 

## Dataset

### Selección de tormentas

Para que el dataset quede completo vamos a usar la metodología Duboski que consiste en buscar registros no nulos de descargas de GLM/WWLLN, ver la media del conteo diario para días con actividad (ojo porque esto hace que cuentes solamente días muy activos) y se queda con días mayores a la media.  

1. **Buscar registros no nulos**: se identifican los registros de GLM/WWLLN que contienen datos de descargas eléctricas, descartando los nulos.

2. **Identificar los días con actividad**: se agrupan los registros por día y se calcula el conteo diario de descargas. Para calcular la media, se consideran únicamente los días que registraron actividad eléctrica (así el conteo es solo sobre días activos).

3. **Calcular la media diaria**: se calcula el promedio del número de descargas entre esos días activos. Por ejemplo, si hubo tres días con 10, 20 y 60 descargas, la media es de 30 descargas diarias.

4. **Seleccionar los días por encima de la media**: se conservan los días cuyo conteo de descargas supera ese promedio. En el ejemplo, se seleccionaría únicamente el día con 60 descargas.

Sobre el punto 4. tengo dudas: debería extenderme un poquito más para no perder registros de tormentas de pequeña escala? perderé núcleos? usamos el p25? 
## IA

### Modelo

*basado en **``Convolutional LSTM Network: A Machine Learning Approach for Precipitation Nowcasting''** https://doi.org/10.48550/arXiv.1506.04214*

La idea es que queremos aprender la evolución de estructuras espacio-temporales. Para eso necesitamos unidades de aprendizaje especializadas en este tipo de estructura, de acá se desprenden las ConvLSTM: una neurona LSTM es una cuya cada estado está definido no solo por el input sino también por los frames previos al mismo siendo este parte de una secuencia temporal. Cada neurona tiene cuatro compuertas que se activan según pesos... Asimismo la estructura espacial es contenida por la arquitectura convolucional. 

### Loss
*basado en ``Weather Radar Echo Extrapolation with Dynamic Weight Loss'' https://doi.org/
10.3390/rs15123138*
Necesitamos definir una función de minimización que sea capaz de conservar estructura, intensidad y evolución. 


$B-MSE(R,\hat{R}) = \sum_{t,h,w} weight_{t,h,w} * {(R_{t,h,w} - \hat{R}_{t,h,w})}^2$


$B-MAE(R,\hat{R}) = \sum_{t,h,w} weight_{t,h,w} * |(R_{t,h,w} - \hat{R}_{t,h,w})|$


donde $
weight_{t,h,w} =
\begin{cases}
0.5  & 0 \leq R_{t,h,w} < 5 \\
1.0  & 5 \leq R_{t,h,w} < 10 \\
2.0  & 10 \leq R_{t,h,w} < 20 \\
5.0  & 20 \leq R_{t,h,w} < 30 \\
10.0 & 30 \leq R_{t,h,w} < 40 \\
20.0 & R_{t,h,w} \geq 40
\end{cases}$

$R_{t,h,w}$ y $\hat{R}_{t,h,w}$ son la reflectividad observada y predicha en las coordenadas (espaciales) $(t,h,w)$ 


Para mejorar el detalle y la resolución de las imagenes de eco de radar, se añade la función: $L_{SSIM} = 1- SSIM$ donde $SSIM$ es la *índice de similaridad estructural* que se expresa como:
$SSIM = \frac{(2\mu_{\Gamma}\mu_{\bar{\Gamma}})(2\sigma_{\Gamma\bar{\Gamma}}+C_2)}{(\mu_{\Gamma}^2 + \mu_{\bar{\Gamma}}^2+C_1)(\sigma_{\Gamma}^2 + \sigma_{\bar{\Gamma}}^2 + C_2)}$

donde $\mu_{\Gamma}$ y $\mu_{\bar{\Gamma}}$ denotan la media de los valores reales y predichos respectivamente, estimando el **brillo** de la imagen; $\sigma_{\Gamma\bar{\Gamma}}$ denota la covarianza entre los valores predichos y medidos midiendo la *similaridad estructural*
de la imagen; y $\sigma_{\Gamma}$ y $\sigma_{\bar{gamma}}$ denota la varianza entre los valores reales y predichos estimando el **contraste** de la imagen. $C_1$ y $C_2$ son dos constantes que evitan dividir por cero. 

Entonces la función de pérdida (*loss function*) pesada queda:

$WL(\hat{y},y) = \beta (B-MSE + B-MAE) + \gamma L_{SSIM}$

Y sumando los pesos dinámicos: 

$ DWL = \sum_{i=1}^m (w_i * WL_i) = \sum_{i=1}^m \left[(\frac{\Delta e_i}{\Delta e_1 + \Delta e_2 + \cdots + \Delta e_m }+1)^2 * W L(\hat{y}_i, y_i)
\right] $

Donde $i$ representa la barrida o *frame* y $\hat{y}_i$ y $y_i$ denotan la imagen predicha y observada en el *frame* $i$, y el peso $w_i$ representa la "dificultad de predicciòn" es decir penaliza màs fuerte a valores predichos mas alejados de la ground truth, se define: 

$w_i = \frac{\Delta e_i}{\Delta e_1 + \Delta e_2 + \cdots + \Delta e_m }+1$ 




El mayor problema con las FC-LSTM a la hora de manejar datos con estructura espacio-temporal es el uso de las conexiones densas en las trancisiones entrada-estado y estado-estado, en las cuales no hay información espacial encodeada. Para sobrellevar este problema una característica distintiva de nuestro diseño es que todos los inputs $X_1, ..., X_t$, los outputs de cada capa $C_1, ... C_t$, los estados ocultos $H_1, ..., H_t$, y las compuertas $i_t, f_t, o_t$ de la ConvLSTM son tensores de 3 dimensiones cuyas últimas dos dimensiones son espaciales (filas y columnas). Para tener una mejor imagen de los inputs y los estados, los podemos imaginar como vectores dentro de una grilla espacial. La ConvLSTM determina el estado futuro de una cierta celda en la grilla con los inputs y los estados anteriores de los vecinos locales. Esto puede ser fácilmente logrado si se usa un operador convolucional en las transiciones de estado a estado y de input a estado. Las ecuaciones clave de una ConvLSTM son: 

$i_t = \sigma(W_{xi} * X_t + W_{hi} * H_{t-1} + W_{ci} \circ C_{t-1} + b_i)$

$f_t = \sigma(W_{xf} * X_t + W_{hf} * H_{t-1} + W_{ci} \circ C_{t-1} + b_i)$

$C_t = f_t \circ C_{t-1} + i_t \circ tanh(W_{xc} * X_t + W_{hc} * H_{t-1} + b_c)$

$o_t = \sigma (W_{xo} * X_t + W_{ho} * H_{t-1} + W_{co} \circ C_t + b_o)$

$H_t = o_t \circ tanh(C_t)$

Notar que el producto de Hadamard (denotado $\circ$) actùa como filtro.


The major drawback of FC-LSTM in handling spatiotemporal data is its usage of full connections in
input-to-state and state-to-state transitions in which no spatial information is encoded. To overcome
this problem, a distinguishing feature of our design is that all the inputs X1 , . . . , Xt , cell outputs
C1 , . . . , Ct, hidden states H1 , . . . , Ht, and gates it , ft , ot of the ConvLSTM are 3D tensors whose
last two dimensions are spatial dimensions (rows and columns). To get a better picture of the inputs
and states, we may imagine them as vectors standing on a spatial grid. The ConvLSTM determines
the future state of a certain cell in the grid by the inputs and past states of its local neighbors.
This can easily be achieved by using a convolution operator in the state-to-state and input-to-state
transitions (see Fig. 2). The key equations of ConvLSTM are shown in (3) below, where ‘∗’ denotes
the convolution operator and ‘◦’, as before, denotes the Hadamard product:
it = σ(Wxi ∗ Xt + Whi ∗ Ht−1 + Wci ◦ Ct−1 + bi )
ft = σ(Wxf ∗ Xt + Whf ∗ Ht−1 + Wcf ◦ Ct−1 + bf )
Ct = ft ◦ Ct−1 + it ◦ tanh(Wxc ∗ Xt + Whc ∗ Ht−1 + bc )
 (3)
ot = σ(Wxo ∗ Xt + Who ∗ Ht−1 + Wco ◦ Ct + bo )
Ht = ot ◦ tanh(Ct)
If we view the states as the hidden representations of moving objects, a ConvLSTM with a larger
transitional kernel should be able to capture faster motions while one with a smaller kernel can
capture slower motions. Also, if we adopt a similar view as [16], the inputs, cell outputs and hidden
states of the traditional FC-LSTM represented by (2) may also be seen as 3D tensors with the last
two dimensions being 1. In this sense, FC-LSTM is actually a special case of ConvLSTM with all
features standing on a single cell.
To ensure that the states have the same number of rows and same number of columns as the inputs,
padding is needed before applying the convolution operation. Here, padding of the hidden states on
the boundary points can be viewed as using the state of the outside world for calculation. Usually,
before the first input comes, we initialize all the states of the LSTM to zero which corresponds to
“total ignorance” of the future. Similarly, if we perform zero-padding (which is used in this paper)
on the hidden states, we are actually setting the state of the outside world to zero and assume no prior
knowledge about the outside. By padding on the states, we can treat the boundary points differently,
which is helpful in many cases. For example, imagine that the system we are observing is a moving
ball surrounded by walls. Although we cannot see these walls, we can infer their existence by finding
the ball bouncing over them again and again, which can hardly be done if the boundary points have
the same state transition dynamics as the inner points.
3.2
 Encoding-Forecasting Structure
Like FC-LSTM, ConvLSTM can also be adopted as a building block for more complex structures.
For our spatiotemporal sequence forecasting problem, we use the structure shown in Fig. 3 which
consists of two networks, an encoding network and a forecasting network. Like in [21], the initial
states and cell outputs of the forecasting network are copied from the last state of the encoding
network. Both networks are formed by stacking several ConvLSTM layers. As our prediction target
has the same dimensionality as the input, we concatenate all the states in the forecasting network
and feed them into a 1 × 1 convolutional layer to generate the final prediction.
We can interpret this structure using a similar viewpoint as [23]. The encoding LSTM compresses
the whole input sequence into a hidden state tensor and the forecasting LSTM unfolds this hidden
4
P rediction
Encoding Network
ConvLST M2
 Copy
 ConvLST M4
ConvLST M1
 Copy
 ConvLST M3
Input
Forecasting Network
Figure 3: Encoding-forecasting ConvLSTM network for precipitation nowcasting
state to give the final prediction:
X̃t+1, . . . , X̃t+K =
 arg ,...,Xt+K
 max p(Xt+1 , . . . , Xt+K | X̂t−J+1 , X̂t−J+2, . . . , X̂t )
Xt+1≈
 arg ,...,Xt+K
 max p(Xt+1 , . . . , Xt+K | fencoding (X̂t−J+1, X̂t−J+2, . . . , X̂t )) (4)
Xt+1≈ gforecasting (fencoding (X̂t−J+1 , X̂t−J+2 , . . . , X̂t ))
This structure is also similar to the LSTM future predictor model in [21] except that our input and
output elements are all 3D tensors which preserve all the spatial information. Since the network has
multiple stacked ConvLSTM layers, it has strong representational power which makes it suitable
for giving predictions in complex dynamical systems like the precipitation nowcasting problem we
study here.