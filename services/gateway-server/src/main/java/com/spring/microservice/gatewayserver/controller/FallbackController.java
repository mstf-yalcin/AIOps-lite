package com.spring.microservice.gatewayserver.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
public class FallbackController {
    @RequestMapping("/accountServiceFallback")
    public Mono<String> accountServiceFallback() {
        return Mono.just("Account Service is taking too long to respond or is down. Please try again later");
    }
}
