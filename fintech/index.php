<?php
$asset_base = 'assets';
$root_prefix = '.';
$page_title = 'Fintech Nova | Inversion digital para empresas';
require_once __DIR__ . '/includes/bootstrap.php';
include 'includes/header.php';
include 'includes/navbar.php';
?>

<main>
    <section class="hero">
        <div class="container hero-shell">
            <div class="hero-copy">
                <span class="eyebrow">Fintech corporativa para capital digital escalable</span>
                <h1>Movemos liquidez, clientes e inversiones desde una sola plataforma.</h1>
                <p>
                    Fintech Nova es una firma ficticia especializada en portafolios empresariales, onboarding financiero
                    y productos de inversion digital. Este sitio servira como base de laboratorio para explicar diseno,
                    construccion y observabilidad de aplicaciones web en PHP.
                </p>

                <div class="hero-actions">
                    <a class="button" href="#contacto">Solicitar demo</a>
                    <a class="button-secondary" href="#productos">Explorar productos</a>
                </div>

                <div class="hero-stats">
                    <article class="stat-card">
                        <span class="stat-value">+180</span>
                        <span class="stat-label">clientes empresariales activos</span>
                    </article>
                    <article class="stat-card">
                        <span class="stat-value">US$92M</span>
                        <span class="stat-label">capital administrado en propuestas</span>
                    </article>
                    <article class="stat-card">
                        <span class="stat-value">12 paises</span>
                        <span class="stat-label">operacion regional de servicios digitales</span>
                    </article>
                </div>
            </div>

            <div class="hero-panel">
                <article class="glass-card hero-board">
                    <span class="panel-heading">Pulse financiero</span>
                    <div class="metric-grid">
                        <div class="metric">
                            <span class="metric-label">Nuevos leads</span>
                            <span class="metric-value">248</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Consultas del dia</span>
                            <span class="metric-value">1.2K</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Portafolios premium</span>
                            <span class="metric-value">68%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Tiempo promedio</span>
                            <span class="metric-value">04m</span>
                        </div>
                    </div>

                    <div class="mini-feed">
                        <div class="feed-item">
                            <div>
                                <strong>Acceso corporativo</strong>
                                <span>Ingreso multicanal desde banca y wealth ops</span>
                            </div>
                            <span class="badge badge-ok">Estable</span>
                        </div>
                        <div class="feed-item">
                            <div>
                                <strong>Propuesta Growth Yield</strong>
                                <span>7 nuevas simulaciones en las ultimas 2 horas</span>
                            </div>
                            <span class="badge badge-warn">Seguimiento</span>
                        </div>
                    </div>
                </article>
            </div>
        </div>
    </section>

    <section class="section-block" id="servicios">
        <div class="container">
            <div class="section-heading">
                <div>
                    <span class="section-kicker">Servicios clave</span>
                    <h2>Operacion financiera digital con una capa comercial clara.</h2>
                </div>
                <p>
                    La version inicial del sitio prioriza una narrativa institucional moderna: venta consultiva,
                    confianza operativa y una base visual que luego podremos conectar al backend en PHP y MySQL.
                </p>
            </div>

            <div class="feature-grid">
                <article class="feature-card">
                    <span class="tile-number">01</span>
                    <h3>Portafolio de clientes</h3>
                    <p>Exhibicion de cuentas corporativas, segmentos y resultados por vertical financiera.</p>
                </article>
                <article class="feature-card">
                    <span class="tile-number">02</span>
                    <h3>Productos fintech</h3>
                    <p>Catalogo de servicios de recaudo, inversion, scoring y cuentas digitales empresariales.</p>
                </article>
                <article class="feature-card">
                    <span class="tile-number">03</span>
                    <h3>Inversion digital</h3>
                    <p>Propuestas de rendimiento, riesgo y horizonte para inversionistas y tesorerias.</p>
                </article>
                <article class="feature-card">
                    <span class="tile-number">04</span>
                    <h3>Trazabilidad operativa</h3>
                    <p>Base para logs de login, consulta, creacion, edicion y eliminacion de registros.</p>
                </article>
            </div>
        </div>
    </section>

    <section class="section-block" id="portafolio">
        <div class="container">
            <div class="section-heading">
                <div>
                    <span class="section-kicker">Clientes</span>
                    <h2>Portafolios empresariales con foco en expansion y eficiencia.</h2>
                </div>
                <p>
                    Estos perfiles son de presentacion. Mas adelante se conectaran a un CRUD administrativo y a tablas
                    de clientes en MySQL.
                </p>
            </div>

            <div class="clients-grid">
                <article class="client-card">
                    <div class="client-logo">AX</div>
                    <h3>Axion Retail Pay</h3>
                    <p>Procesamiento de cobros recurrentes y conciliacion para retail regional.</p>
                    <span class="tag">Retail payments</span>
                </article>
                <article class="client-card">
                    <div class="client-logo">BN</div>
                    <h3>Banco Nexo Capital</h3>
                    <p>Portafolio digital para wealth management y propuestas de inversion semiautomatizadas.</p>
                    <span class="tag">Private banking</span>
                </article>
                <article class="client-card">
                    <div class="client-logo">QV</div>
                    <h3>Quantum Ventures</h3>
                    <p>Analitica comercial y seguimiento de oportunidades de inversion de alto crecimiento.</p>
                    <span class="tag">Investment ops</span>
                </article>
            </div>
        </div>
    </section>

    <section class="section-block" id="productos">
        <div class="container">
            <div class="section-heading">
                <div>
                    <span class="section-kicker">Productos</span>
                    <h2>Una arquitectura comercial pensada para pagos, analitica y rendimiento.</h2>
                </div>
                <p>
                    La capa publica ya puede presentar los productos antes de que implementemos el panel de administracion
                    para mantenerlos por base de datos.
                </p>
            </div>

            <div class="products-grid">
                <article class="product-card featured">
                    <span class="tag">Flagship</span>
                    <h3>Nova Treasury Hub</h3>
                    <p>Panel para tesoreria corporativa con saldos multiempresa, proyecciones y alertas de flujo.</p>
                    <ul class="bullet-list">
                        <li>Concentracion de cuentas</li>
                        <li>Monitoreo de movimientos</li>
                        <li>Panel ejecutivo en tiempo real</li>
                    </ul>
                </article>
                <article class="product-card">
                    <span class="tag">Growth</span>
                    <h3>Yield Bridge</h3>
                    <p>Propuestas de inversion digital orientadas a capital de trabajo y excedentes de caja.</p>
                    <ul class="bullet-list">
                        <li>Riesgo segmentado</li>
                        <li>Horizontes flexibles</li>
                        <li>Simulacion de retorno esperado</li>
                    </ul>
                </article>
                <article class="product-card">
                    <span class="tag">Data</span>
                    <h3>Signal Score API</h3>
                    <p>Motor de scoring y observacion de comportamiento para clientes y operaciones sensibles.</p>
                    <ul class="bullet-list">
                        <li>Perfiles de actividad</li>
                        <li>Eventos de acceso y consulta</li>
                        <li>Integracion con trazas futuras</li>
                    </ul>
                </article>
            </div>
        </div>
    </section>

    <section class="section-block" id="inversiones">
        <div class="container">
            <div class="section-heading">
                <div>
                    <span class="section-kicker">Inversion digital</span>
                    <h2>Propuestas listas para convertirse en escenarios de negocio y de laboratorio.</h2>
                </div>
                <p>
                    Esta seccion prepara el terreno para el modulo de propuestas de inversion, sus consultas y su
                    trazabilidad posterior dentro del sistema.
                </p>
            </div>

            <div class="timeline-grid">
                <article class="timeline-card">
                    <span class="tag">Conservador</span>
                    <h3>Stable Income 360</h3>
                    <p>Vehiculo de renta fija digital para companias con horizonte corto y control de volatilidad.</p>
                </article>
                <article class="timeline-card">
                    <span class="tag">Balanceado</span>
                    <h3>Hybrid Growth Notes</h3>
                    <p>Canasta con exposicion moderada a deuda corporativa, fondos estructurados y liquidez tactica.</p>
                </article>
                <article class="timeline-card">
                    <span class="tag">Expansivo</span>
                    <h3>Frontier Alpha Grid</h3>
                    <p>Estrategia de crecimiento para inversionistas que aceptan mas riesgo a cambio de retornos proyectados superiores.</p>
                </article>
            </div>
        </div>
    </section>

    <section class="section-block" id="contacto">
        <div class="container contact-shell">
            <article class="contact-card highlight">
                <span class="section-kicker">Contacto</span>
                <h3>Solicita una presentacion ejecutiva</h3>
                <p>
                    En la siguiente fase este formulario podra persistir mensajes en MySQL y generar eventos para el log
                    de actividad. Por ahora queda listo el frontend de entrada.
                </p>
                <form class="contact-form" action="#" method="post">
                    <input type="text" name="name" placeholder="Nombre completo">
                    <input type="email" name="email" placeholder="Correo corporativo">
                    <input type="text" name="company" placeholder="Empresa">
                    <textarea name="message" placeholder="Cuentanos que tipo de producto o inversion te interesa"></textarea>
                    <button class="button" type="submit">Enviar consulta</button>
                </form>
            </article>

            <article class="contact-card">
                <span class="section-kicker">Cobertura regional</span>
                <h3>Atencion especializada para banca, wealth y corporate finance.</h3>
                <ul class="contact-list">
                    <li>Onboarding empresarial en menos de 48 horas.</li>
                    <li>Portafolio digital para clientes premium y middle market.</li>
                    <li>Canal de seguimiento comercial para equipos de advisory.</li>
                    <li>Base lista para agregar autenticacion, CRUD y logs de eventos.</li>
                </ul>
            </article>
        </div>
    </section>
</main>

<?php include 'includes/footer.php'; ?>
