package com.spring.microservice.gatewayserver.filters;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
public class ResponseTraceFilter implements GlobalFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        return chain.filter(exchange).then(Mono.fromRunnable(() -> {
            HttpHeaders requestHeaders = exchange.getRequest().getHeaders();
            String correlationId = filterUtility.getCorrelationId(requestHeaders);

            if (!exchange.getResponse().getHeaders().containsKey(filterUtility.CORRELATION_ID)) {
                logger.debug("Updated the correlation id to the outbound headers: {}", correlationId);
                exchange.getResponse().getHeaders().add(filterUtility.CORRELATION_ID, correlationId);
            }
        }));
    }


    private static final Logger logger = LoggerFactory.getLogger(ResponseTraceFilter.class);
    private final FilterUtility filterUtility;

    public ResponseTraceFilter(FilterUtility filterUtility) {
        this.filterUtility = filterUtility;
    }

//    @Bean
//    public GlobalFilter postGlobalFilter() {
//        return (exchange, chain) -> {
//            return chain.filter(exchange).then(Mono.fromRunnable(() -> {
//                HttpHeaders requestHeaders = exchange.getRequest().getHeaders();
//                String correlationId = filterUtility.getCorrelationId(requestHeaders);
//                logger.debug("Updated the correlation id to the outbound headers: {}", correlationId);
//                exchange.getResponse().getHeaders().add(filterUtility.CORRELATION_ID, correlationId);
//            }));
//        };
//    }
}
