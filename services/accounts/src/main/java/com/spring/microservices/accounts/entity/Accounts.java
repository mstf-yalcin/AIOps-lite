package com.spring.microservices.accounts.entity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import lombok.*;

@Entity
@Data
@EqualsAndHashCode(callSuper = true)
@AllArgsConstructor
@NoArgsConstructor
@ToString(exclude = "customer")
public class Accounts extends BaseEntity {

    //account number

    private String accountType;

    private String branchAddress;

    @OneToOne()
    @JoinColumn(name = "customer_id")
    private Customer customer;

    public Accounts(String accountType, String branchAddress) {
        this.accountType = accountType;
        this.branchAddress = branchAddress;
    }

    //    @Column(name = "customer_id")
//    private Long customerId;

}
