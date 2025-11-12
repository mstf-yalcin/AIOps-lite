package com.spring.microservices.accounts.mapper;

import com.spring.microservices.accounts.dto.AccountsDto;
import com.spring.microservices.accounts.entity.Accounts;

public class AccountsMapper {

    public static AccountsDto toDto(Accounts accounts) {
        AccountsDto accountsDto = new AccountsDto();
        accountsDto.setAccountNumber(accounts.getId());
        accountsDto.setAccountType(accounts.getAccountType());
        accountsDto.setBranchAddress(accounts.getBranchAddress());
        return accountsDto;
    }

    public static Accounts toEntity(AccountsDto accountsDto) {
        Accounts accounts = new Accounts();
        accounts.setId(accountsDto.getAccountNumber());
        accounts.setAccountType(accountsDto.getAccountType());
        accounts.setBranchAddress(accountsDto.getBranchAddress());
        return accounts;
    }

}
